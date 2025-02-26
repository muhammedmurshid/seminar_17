from odoo import models, fields, api, _


class BulkSeminarDataAssign(models.TransientModel):
    _name = 'bulk.seminar.assign'
    _description = 'Bulk Seminar Data Assign'

    seminar_id = fields.Many2one('seminar.leads', string='Seminar')
    lead_user_ids = fields.Many2many('res.users', string='Lead Users')

    @api.onchange('seminar_id')
    def _onchange_leads_users(self):
        users = self.env.ref('custom_leads.group_lead_users').users
        lead_users = users.ids  # Get list of IDs directly
        self.lead_user_ids = [(6, 0, lead_users)]  # Assign to Many2many field
        return {'domain': {'user_id': [('id', 'in', lead_users)]}}


    user_id = fields.Many2one('res.users', string='Assign To',)

    def action_assign(self):
        lead = self.env['leads.logic'].sudo().search([('seminar_id', '=', self.seminar_id.id)])
        for rec in lead:
            if rec:
                if rec.admission_status == False:
                    rec.update({
                        'lead_owner': self.user_id.employee_id.id,
                        'state': 'in_progress',
                        'assigned_date': fields.Datetime.now()
                    })
            # seminar_data = self.env['seminar.students'].sudo().search([('id', '=', rec.seminar_lead_id)])
            # for j in seminar_data:
            #     print(j.seminar_id, 'rec')
            #     print(rec.id, 'lead')
            #     rec.update({
            #         'leads_assign': self.user_id.employee_id.id,
            #         'state': 'confirm'
            #     })

                # rec.activity_schedule('leads.mail_seminar_leads_done', user_id=self.user_id.id)

            # rec.lead_assign = self.user_id.employee_id.id
        self.seminar_id.bulk_lead_assign = True
        self.seminar_id.state = 'leads_assigned'
        self.seminar_id.assigned_user = self.user_id.id

    def action_assign_without_assign(self):
        lead = self.env['leads.logic'].sudo().search([('seminar_id', '=', self.seminar_id.id)])

        for rec in lead:
            if rec:
                if not rec.lead_owner:
                    if rec.admission_status == False:
                        rec.update({
                            'lead_owner': self.user_id.employee_id.id,
                            'state': 'in_progress',
                            'assigned_date': fields.Datetime.now()
                        })

        self.seminar_id.bulk_lead_assign = True
        self.seminar_id.state = 'leads_assigned'
        self.seminar_id.assigned_user = self.user_id.id


    def action_add_tele_callers(self):
        lead = self.env['leads.logic'].sudo().search([('seminar_id', '=', self.seminar_id.id)])

        for rec in lead:
            if rec:
                if rec.admission_status == False:
                    rec.update({
                        'lead_owner': False,
                        'state': 'in_progress',
                        'tele_caller_id': self.user_id.id,
                        'lead_quality': 'new'
                    })

        self.seminar_id.bulk_lead_assign = True
        self.seminar_id.state = 'leads_assigned'
        self.seminar_id.assigned_user = self.user_id.id


