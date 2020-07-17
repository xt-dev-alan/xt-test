from odoo import http
import json
from odoo.http import request
from datetime import datetime, date


class QueryBuilder(http.Controller):

    @http.route('/api_bi/records/data/', auth='connector_bi', type='json', cors='*', methods=['POST'])
    def field_data(self, fields, model, limit, page):
        page = int(page)
        limit = int(limit)
        headers = {'Content-Type': 'application/json'}
        return self.get_query(fields, model, limit, page)
        # return json.dumps(result, default=self.datetime_serializer)

    def get_query(self, fields, model, limit=10, page=1, order=None):
        if order is None:
            order = ['id ASC']
        order = ', '.join(order)
        offset = (page - 1) * limit
        table = model['model'].replace('.', '_')
        sql = """
            SELECT count(*) from {}
        """.format(table)
        request.cr.execute(sql)
        total = request.cr.fetchone()[0]
        search = request.env[model['model']].search([], order=order, offset=offset, limit=limit)

        field_names = [field['name'] for field in fields]
        field_descriptions = [field['field_description'] for field in fields]
        results = []
        for row in search:
            for field in row.read(field_names):
                results.append(field)

        return {'data': results, 'total': total}

    def datetime_serializer(self, object):
        if isinstance(object, datetime) | isinstance(object, date):
            return object.__str__()

    @http.route('/api_bi/chart/', auth='connector_bi', type='json', cors='*', methods=['POST'])
    def chart_data_column(self, fields, model, dimension, measure, chart_type):
        fields = [field for field in fields if field['id'] in [dimension, measure]]
        headers = {'Content-Type': 'application/json'}
        result = self.get_query_chart(fields, model, dimension, measure)
        result['type'] = chart_type
        return result

    def get_query_chart(self, fields, model, dimension, measure, order=None):
        if order is None:
            order = ['id ASC']
        order = ', '.join(order)
        search = request.env[model['model']].search([], order=order, limit=1000)

        field_names = [field['name'] for field in fields]
        field_descriptions = [field['field_description'] for field in fields]
        results = {}
        dimension = [field for field in fields if field['id'] == dimension][0]
        measure = [field for field in fields if field['id'] == measure][0]
        for row in search:
            for record in row.read(field_names):
                dimension_value = record[dimension['name']] if not isinstance(record[dimension['name']], tuple) \
                    else record[dimension['name']][1]
                if dimension_value not in results:
                    results[dimension_value] = 0
                results[dimension_value] += record[measure['name']]

        results = [{'label': dimension, 'value': results[dimension]} for dimension in results]
        title = "{}: {} per {}".format(model['name'], measure['field_description'], dimension['field_description'])
        return {'result': results, 'axis_x_name': dimension['field_description'],
                'axis_y_name': measure['field_description'], 'title': title}

    @http.route('/api_bi/query/chart/pie2d/', auth='public', type='http', cors='*', methods=['POST'], csrf=False)
    def chart_data_pie(self, fields, model, dimension, measure, type):
        return self.chart_data_column(fields, model, dimension, measure, type)

    @http.route('/api_bi/query/chart/line/', auth='public', type='http', cors='*', methods=['POST'], csrf=False)
    def chart_data_line(self, fields, model, dimension, measure, type):
        return self.chart_data_column(fields, model, dimension, measure, type)

    @http.route('/api_bi/query/chart/spline/', auth='public', type='http', cors='*', methods=['POST'], csrf=False)
    def chart_data_spline(self, fields, model, dimension, measure, type):
        return self.chart_data_column(fields, model, dimension, measure, type)

    @http.route('/api_bi/query/chart/area2d/', auth='public', type='http', cors='*', methods=['POST'], csrf=False)
    def chart_data_area2d(self, fields, model, dimension, measure, type):
        return self.chart_data_column(fields, model, dimension, measure, type)