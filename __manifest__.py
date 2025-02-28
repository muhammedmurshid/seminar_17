{
    'name': "Seminar",
    'version': '1.0',
    'depends': ['base', 'web', 'custom_leads',],
    'author': "Murshid",
    'category': 'Category',
    'description': """
    Description text
    """,
    # data files always loaded at installation
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/rules.xml',
        'views/leads.xml',
        'views/institute.xml',
        'views/bulk_data_assign.xml',
        'views/expenses.xml',
        'views/km_traveling_rate.xml'
        # 'views/data_assigning.xml'
    ],
    # data files containing optionally loaded demonstration data
    'demo': [
        # 'demo/demo_data.xml',
    ],
    'images': [
        'static/description/icon.png',
    ],
}
