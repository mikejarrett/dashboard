# -*- coding: utf-8 -*-
from datetime import datetime, timezone, timedelta

import requests


class TFLClient:

    def __init__(self, base_url, app_id, app_key):
        self.base_url = base_url
        self.app_id = app_id
        self.app_key = app_key

    def get_now(self):
        now = datetime.utcnow()
        return now.replace(tzinfo=timezone(timedelta(hours=0)))

    def get(self, uri, params=None):
        if params is None:
            params = {}

        params.update({
            'app_id': self.app_id,
            'app_key': self.app_key,
        })
        url = '{base_url}{uri}'.format(base_url=self.base_url, uri=uri)
        return requests.get(url, params)

    def get_bus_arrival_countdown(self, bus_number, stop_id):
        uri = '/Line/{bus_number}/Arrivals'.format(bus_number=bus_number)
        params = {'stopPointId': stop_id}
        raw_response = self.get(uri, params)

        countdown = []
        for obj in raw_response.json():
            expected = self.get_expected(obj)
            time_delta = expected - self.get_now()
            eta = time_delta.total_seconds() // 60
            if eta > 0:
                countdown.append(eta)

        return sorted(countdown)

    def get_expected(self, obj):
        return datetime.strptime(
            obj['expectedArrival'].split('.')[0] + 'Z', "%Y-%m-%dT%H:%M:%SZ"
        ).replace(tzinfo=timezone(timedelta(hours=0)))

    def get_specific_line_statuses(self, line_ids):
        uri = '/Line/{ids}/Status'.format(ids=','.join(line_ids))

        raw_response = self.get(uri)

        content = raw_response.json()

        response = {}
        for obj in content:
            response[obj['name']] = self._get_status(obj)

        return response

    def _get_status(self, obj):
        statuses = []

        for line_status in obj['lineStatuses']:
            status = line_status.get('disruption', {})
            statuses.append({
                'created': status.get('created'),
                'info': status.get('additionalInfo'),
                'status': line_status['statusSeverityDescription'],
                'status_id': line_status['statusSeverity'],
            })

        if not statuses:
            statuses = [{
                'created': None,
                'info': None,
                'status': 'UNKNOWN',
                'status_id': 99,
            }]

        return statuses
