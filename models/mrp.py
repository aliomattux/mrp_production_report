from operator import itemgetter
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, AccessError
from pprint import pprint as pp
import re

class MrpProduction(models.Model):
    _inherit = 'mrp.production'


    @api.one
    def get_sorted_lines(self):
        res_move_lines = []
        for line in self.move_raw_ids:
            move_lines = line.move_line_ids.filtered(lambda x: x.state != 'done' and x.product_qty)
            if self.state == 'done':
                move_lines = line.move_line_ids.filtered(lambda x: x.state == 'done' and x.qty_done)

            for ml in move_lines:
#                res_move_lines.append(ml)
                res_move_lines.append({
                    'product_name': ml.product_id.name,
                    'sku': ml.product_id.default_code,
                    'qty': ml.product_uom_qty,
                    'qty_done': ml.qty_done,
                    'line_state': ml.state,
                    'product_uom': ml.product_uom_id.name,
                    'location': ml.location_id.name,
                    'lot_id': ml.lot_id.name,
                    'lot_name': ml.lot_name,
                    'product_barcode': ml.product_id.barcode,
                })

        res = self.sorted_nicely(res_move_lines, itemgetter('location'))
        return res_move_lines


    def sorted_nicely(self, l, key):
        convert = lambda text: int(text) if text.isdigit() else text
        alphanum_key = lambda item: [ convert(c) for c in re.split('([0-9]+)', key(item)) ]
        return sorted(l, key = alphanum_key)
