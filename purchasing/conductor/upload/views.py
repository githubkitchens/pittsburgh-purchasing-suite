# -*- coding: utf-8 -*-

import os

from flask import (
    Blueprint, request, current_app, render_template,
    jsonify, redirect, url_for, flash
)
from werkzeug import secure_filename

from purchasing.utils import connect_to_s3, upload_file
from purchasing.database import db
from purchasing.data.models import ContractBase
from purchasing.data.importer.costars import main as import_costars
from purchasing.decorators import requires_roles
from purchasing.conductor.forms import FileUploadForm, ContractUploadForm

blueprint = Blueprint(
    'conductor_uploads', __name__, url_prefix='/conductor/upload',
    template_folder='../templates'
)

@blueprint.route('/costars', methods=['GET', 'POST'])
@requires_roles('conductor', 'admin', 'superadmin')
def upload_costars():
    form = FileUploadForm()
    if form.validate_on_submit():
        _file = request.files.get('upload')
        filename = secure_filename(_file.filename)
        filepath = os.path.join(current_app.config.get('UPLOAD_FOLDER'), filename)
        try:
            _file.save(filepath)
        except IOError:
            # if the upload folder doesn't exist, create it then save
            os.mkdir(current_app.config.get('UPLOAD_FOLDER'))
            _file.save(filepath)
        return render_template(
            'conductor/upload/upload_success.html',
            filepath=filepath, filename=filename
        )
    else:
        return render_template('conductor/upload/upload_new.html', form=form)

@blueprint.route('/costars/_process', methods=['POST'])
@requires_roles('conductor', 'admin', 'superadmin')
def process_costars_upload():

    filepath = request.form.get('filepath')
    filename = request.form.get('filename')
    delete = request.form.get('_delete')

    try:
        import_costars(filepath, filename, None, None, None)

        if delete not in ['False', 'false', False]:
            os.remove(filepath)

        return jsonify({'status': 'success'}), 200

    except Exception, e:
        raise e
        return jsonify({'status': 'error: {}'.format(e)}), 500

def upload_costars_contract(_file):
    filename = secure_filename(_file.filename)

    if current_app.config['UPLOAD_S3']:
        conn, bucket = connect_to_s3(
            current_app.config['AWS_ACCESS_KEY_ID'],
            current_app.config['AWS_SECRET_ACCESS_KEY'],
            'costars'
        )

        file_href = upload_file(filename, bucket, prefix='/')
        return filename, file_href

    else:
        try:
            os.mkdir(current_app.config['UPLOAD_DESTINATION'])
        except:
            pass

        filepath = os.path.join(current_app.config['UPLOAD_DESTINATION'], filename)
        _file.save(filepath)
        return filename, filepath

@blueprint.route('/costars/contracts', methods=['GET', 'POST'])
@requires_roles('conductor', 'admin', 'superadmin')
def costars_contract_upload():
    contracts = ContractBase.query.filter(
        db.func.lower(ContractBase.contract_type) == 'costars',
        db.or_(
            ContractBase.contract_href == None,
            ContractBase.contract_href == ''
        )
    ).all()

    form = ContractUploadForm()

    if form.validate_on_submit():
        _file = request.files.get('upload')
        filename, filepath = upload_costars_contract(_file)

        contract = ContractBase.query.get(int(form.data.get('contract_id')))

        contract.update(contract_href=filepath)
        flash('Contract uploaded successfully', 'alert-success')
        return redirect(url_for('conductor_uploads.costars_contract_upload'))

    return render_template(
        '/conductor/upload/upload_costars_documents.html',
        form=form, contracts=contracts
    )