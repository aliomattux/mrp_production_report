from operator import itemgetter
from datetime import datetime
import re
from odoo import tools
from odoo import api, fields, models
from pprint import pprint as pp

class ProductionLocationReport(models.AbstractModel):
    _name = 'report.mrp.report_mrporder'
    _description = 'Production Order'

    @api.multi
    def _get_report_values(self, docids, data=None):
        mrp_model = self.env['mrp.production']
        production_orders = mrp_model.browse(docids)
        res = {}
        mos = self.env['mrp.production'].browse(docids)
        for mo in mos:
            vals = self._prepare_mo_values(mo)
            res[mo.id] = vals

        return {
            'doc_ids': docids,
            'doc_model': 'mrp.production',
            'docs': production_orders,
            'res': res,
        }

    def _prepare_mo_values(self, mo):
        workorders = []
        has_product_available = False
        has_product_reserved = False
        has_location = False
        has_serial_number = False
        has_product_barcode = False

        dp = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        for line in mo.move_raw_ids:
            if line.product_id.barcode:
                has_product_barcode = True

            if round(line.product_uom_qty, dp) != round(line.reserved_availability, dp):
                has_product_reserved = True

            for ml in line.move_line_ids:
                if ml.product_qty > 0:
                    has_product_available = True
                elif mo.state == 'done' and ml.qty_done > 0:
                    has_product_available = True
                if ml.lot_id or ml.lot_name:
                    has_serial_number = True
                if ml.location_id:
                    has_location = True

        for wo in mo.workorder_ids:
            workorders.append({
                'name': wo.name,
                'workcenter': wo.workcenter_id.name,
                'duration_expected': wo.duration_expected,
                'duration': wo.duration,
            })

        vals = {
            'state': mo.state,
            'name': mo.name,
            'origin': mo.origin,
            'user_name': mo.user_id.name,
            'date_planned_start': mo.date_planned_start,
            'date_planned_finished': mo.date_planned_finished,
            'product': mo.product_id.name,
            'product_qty': mo.product_qty,
            'product_uom': mo.product_uom_id.name,
            'workorders': workorders,
            'raw_moves': self.get_sorted_lines(mo),
            'has_product_available': has_product_available,
            'has_product_reserved': has_product_reserved,
            'has_location': has_location,
            'has_serial_number': has_serial_number,
            'has_product_barcode': has_product_barcode,
        }

        pp(vals)
        return vals


    def get_sorted_lines(self, mo):
        res_move_lines = []
        for line in mo.move_raw_ids:
            move_lines = line.move_line_ids.filtered(lambda x: x.state != 'done' and x.product_qty)
            if mo.state == 'done':
                move_lines = line.move_line_ids.filtered(lambda x: x.state == 'done' and x.qty_done)

            for ml in move_lines:
#                res_move_lines.append(ml)
                res_move_lines.append({
                    'product_name': ml.product_id.name,
                    'sku': ml.product_id.default_code,
                    'qty': ml.product_uom_qty,
                    'product_other_qty': ml.product_qty,
                    'qty_done': ml.qty_done,
                    'line_state': ml.state,
                    'product_uom': ml.product_uom_id.name,
                    'location': ml.location_id.name,
                    'lot_id': ml.lot_id.name,
                    'lot_name': ml.lot_name,
                    'state': ml.state,
                    'product_barcode': ml.product_id.barcode,
                })

        res = self.sorted_nicely(res_move_lines, itemgetter('location'))
        return res


    def sorted_nicely(self, l, key):
        convert = lambda text: int(text) if text.isdigit() else text
        alphanum_key = lambda item: [ convert(c) for c in re.split('([0-9]+)', key(item)) ]
        return sorted(l, key = alphanum_key)
