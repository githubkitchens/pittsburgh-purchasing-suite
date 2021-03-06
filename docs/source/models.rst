Models
======

Base Models and Mixins
----------------------

Model
"""""

.. autoclass:: purchasing.database.Model
    :members:

.. autofunction:: purchasing.database.get_or_create

RefreshSearchViewMixin
""""""""""""""""""""""

.. autoclass:: purchasing.database.RefreshSearchViewMixin
    :members:


Scout and Conductor
-------------------

Contracts
"""""""""

.. autoclass:: purchasing.data.contracts.ContractBase
    :members:

.. autoclass:: purchasing.data.contracts.ContractType
    :members:

.. autoclass:: purchasing.data.contracts.ContractProperty
    :members:

.. autoclass:: purchasing.data.contracts.LineItem
    :members:

Companies
"""""""""

.. autoclass:: purchasing.data.companies.Company
    :members:

.. autoclass:: purchasing.data.companies.CompanyContact
    :members:

Searches
""""""""

.. automodule:: purchasing.data.searches
    :members:

Stages
""""""

.. autoclass:: purchasing.data.stages.Stage
    :members:

Flows
"""""

.. autoclass:: purchasing.data.flows.Flow
    :members:

.. _contract-stages:

Contract Stages
"""""""""""""""

.. autoclass:: purchasing.data.contract_stages.ContractStage
    :members:

.. autoclass:: purchasing.data.contract_stages.ContractStageActionItem
    :members:

Beacon
------

Opportunities
"""""""""""""

.. autoclass:: purchasing.opportunities.models.Opportunity
    :members:

.. autoclass:: purchasing.opportunities.models.OpportunityDocument
    :members:

.. autoclass:: purchasing.opportunities.models.RequiredBidDocument
    :members:

Vendors
"""""""

.. autoclass:: purchasing.opportunities.models.Vendor
    :members:

Categories
""""""""""

.. autoclass:: purchasing.opportunities.models.Category
    :members:

Public and User
---------------

Users
"""""

.. autoclass:: purchasing.users.models.User
    :members:

.. autoclass:: purchasing.users.models.Role
    :members:

.. autoclass:: purchasing.users.models.Department
    :members:

.. autoclass:: purchasing.users.models.AnonymousUser
    :members:

App Status
""""""""""

.. autoclass:: purchasing.public.models.AppStatus
    :members:

.. autoclass:: purchasing.public.models.AcceptedEmailDomains
    :members:

Job Status
""""""""""

.. autoclass:: purchasing.jobs.job_base.JobStatus
    :members:

.. _sqla query: http://docs.sqlalchemy.org/en/rel_1_0/orm/query.html#the-query-object
.. _TSVECTOR: http://www.postgresql.org/docs/9.4/static/datatype-textsearch.html
