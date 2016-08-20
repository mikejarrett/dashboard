# -*- coding: utf-8 -*-
from datetime import datetime, timezone, timedelta
from unittest import TestCase, mock
import json
import re

import responses

from dashboard.clients import TFLClient


LINE_STATUS_RESPONSE = r"""[{"$type":"Tfl.Api.Presentation.Entities.Line, Tfl.Api.Presentation.Entities","id":"central","name":"Central","modeName":"tube","disruptions":[],"created":"2016-08-10T12:45:22.153Z","modified":"2016-08-10T12:45:22.153Z","lineStatuses":[],"routeSections":[],"serviceTypes":[{"$type":"Tfl.Api.Presentation.Entities.LineServiceTypeInfo, Tfl.Api.Presentation.Entities","name":"Regular","uri":"/Line/Route?ids=Central&serviceTypes=Regular"},{"$type":"Tfl.Api.Presentation.Entities.LineServiceTypeInfo, Tfl.Api.Presentation.Entities","name":"Night","uri":"/Line/Route?ids=Central&serviceTypes=Night"}]},{"$type":"Tfl.Api.Presentation.Entities.Line, Tfl.Api.Presentation.Entities","id":"northern","name":"Northern","modeName":"tube","disruptions":[],"created":"2016-08-10T12:45:22.247Z","modified":"2016-08-10T12:45:22.247Z","lineStatuses":[{"$type":"Tfl.Api.Presentation.Entities.LineStatus, Tfl.Api.Presentation.Entities","id":0,"statusSeverity":10,"statusSeverityDescription":"Good Service","created":"0001-01-01T00:00:00","validityPeriods":[]}],"routeSections":[],"serviceTypes":[{"$type":"Tfl.Api.Presentation.Entities.LineServiceTypeInfo, Tfl.Api.Presentation.Entities","name":"Regular","uri":"/Line/Route?ids=Northern&serviceTypes=Regular"}]},{"$type":"Tfl.Api.Presentation.Entities.Line, Tfl.Api.Presentation.Entities","id":"south-west-trains","name":"South West Trains","modeName":"national-rail","disruptions":[],"created":"2016-08-10T12:45:22.17Z","modified":"2016-08-10T12:45:22.17Z","lineStatuses":[{"$type":"Tfl.Api.Presentation.Entities.LineStatus, Tfl.Api.Presentation.Entities","id":0,"lineId":"south-west-trains","statusSeverity":9,"statusSeverityDescription":"Minor Delays","reason":"http://www.nationalrail.co.uk/service_disruptions/145919.aspx","created":"0001-01-01T00:00:00","validityPeriods":[{"$type":"Tfl.Api.Presentation.Entities.ValidityPeriod, Tfl.Api.Presentation.Entities","fromDate":"2016-08-18T19:36:00Z","isNow":false}],"disruption":{"$type":"Tfl.Api.Presentation.Entities.Disruption, Tfl.Api.Presentation.Entities","category":"Information","categoryDescription":"Information","description":"http://www.nationalrail.co.uk/service_disruptions/145919.aspx","additionalInfo":"Disruption  between Barnes / Clapham Junction and London Waterloo until approximately 21:00","created":"2016-08-18T19:36:00Z","affectedRoutes":[],"affectedStops":[],"closureText":"minorDelays"}}],"routeSections":[],"serviceTypes":[{"$type":"Tfl.Api.Presentation.Entities.LineServiceTypeInfo, Tfl.Api.Presentation.Entities","name":"Regular","uri":"/Line/Route?ids=South West Trains&serviceTypes=Regular"}]},{"$type":"Tfl.Api.Presentation.Entities.Line, Tfl.Api.Presentation.Entities","id":"victoria","name":"Victoria","modeName":"tube","disruptions":[],"created":"2016-08-10T12:45:22.153Z","modified":"2016-08-10T12:45:22.153Z","lineStatuses":[{"$type":"Tfl.Api.Presentation.Entities.LineStatus, Tfl.Api.Presentation.Entities","id":0,"statusSeverity":10,"statusSeverityDescription":"Good Service","created":"0001-01-01T00:00:00","validityPeriods":[]}],"routeSections":[],"serviceTypes":[{"$type":"Tfl.Api.Presentation.Entities.LineServiceTypeInfo, Tfl.Api.Presentation.Entities","name":"Regular","uri":"/Line/Route?ids=Victoria&serviceTypes=Regular"},{"$type":"Tfl.Api.Presentation.Entities.LineServiceTypeInfo, Tfl.Api.Presentation.Entities","name":"Night","uri":"/Line/Route?ids=Victoria&serviceTypes=Night"}]}]"""
BUS_93_ARRIVAL_RESPONSE = r"""[{"$type":"Tfl.Api.Presentation.Entities.Prediction, Tfl.Api.Presentation.Entities","id":"-878559136","operationType":1,"vehicleId":"BT65JGO","naptanId":"490008948N1","stationName":"Langley Avenue","lineId":"93","lineName":"93","platformName":"HK","direction":"outbound","bearing":"28","destinationNaptanId":"","destinationName":"Putney Bridge","timestamp":"2016-08-18T18:17:21Z","timeToStation":820,"currentLocation":"","towards":"Morden or Sutton Common","expectedArrival":"2016-08-18T18:31:01.6339576Z","timeToLive":"2016-08-18T18:31:31.6339576Z","modeName":"bus"},{"$type":"Tfl.Api.Presentation.Entities.Prediction, Tfl.Api.Presentation.Entities","id":"-1046968362","operationType":1,"vehicleId":"LX58CXA","naptanId":"490008948N1","stationName":"Langley Avenue","lineId":"93","lineName":"93","platformName":"HK","direction":"outbound","bearing":"28","destinationNaptanId":"","destinationName":"Putney Bridge","timestamp":"2016-08-18T18:17:21Z","timeToStation":1420,"currentLocation":"","towards":"Morden or Sutton Common","expectedArrival":"2016-08-18T18:41:01.6339576Z","timeToLive":"2016-08-18T18:41:31.6339576Z","modeName":"bus"},{"$type":"Tfl.Api.Presentation.Entities.Prediction, Tfl.Api.Presentation.Entities","id":"2088432762","operationType":1,"vehicleId":"LX58CXE","naptanId":"490008948N1","stationName":"Langley Avenue","lineId":"93","lineName":"93","platformName":"HK","direction":"outbound","bearing":"28","destinationNaptanId":"","destinationName":"Putney Bridge","timestamp":"2016-08-18T18:17:21Z","timeToStation":125,"currentLocation":"","towards":"Morden or Sutton Common","expectedArrival":"2016-08-18T18:19:26.6339576Z","timeToLive":"2016-08-18T18:19:56.6339576Z","modeName":"bus"}]"""


class TFLClientInterface:

    maxDiff = None

    def test_get_specific_line_statuses(self):
        response = self.tfl_client.get_specific_line_statuses(
            [
                'northern',
                'victoria',
                'central',
                'south-west-trains',
            ]
        )

        expected = {
            'Northern': [{
                'created': None,
                'info': None,
                'status': 'Good Service',
                'status_id': 10,
            }],
            'Victoria': [{
                'created': None,
                'info': None,
                'status': 'Good Service',
                'status_id': 10,
            }],
            'Central': [{
                'created': None,
                'info': None,
                'status': 'UNKNOWN',
                'status_id': 99,
            }],
            'South West Trains': [{
                'created': '2016-08-18T19:36:00Z',
                'info': (
                    'Disruption  between Barnes / Clapham Junction '
                    'and London Waterloo until approximately 21:00'
                ),
                'status': 'Minor Delays',
                'status_id': 9,
            }]
        }

        self.assertEqual(response, expected)

    def test_get_bus_arrival_countdown(self):
        now = datetime(2016, 8, 18, 18, 30, 00)
        now = now.replace(tzinfo=timezone(timedelta(hours=0)))
        mock_now = mock.Mock(return_value=now)
        with mock.patch.object(self.tfl_client, 'get_now', mock_now):
            response = self.tfl_client.get_bus_arrival_countdown(93, '490008948N1')

        expected = [1.0, 11.0]

        self.assertEqual(response, expected)


class TestTFLClient(TFLClientInterface, TestCase):

    tfl_client = TFLClient('http://fake.example.com', 'fake-id', 'fake-id')

    @classmethod
    def setUpClass(cls):
        responses.add(
            responses.GET,
            re.compile('.*Line/.*/Arrivals.*'),
            body=BUS_93_ARRIVAL_RESPONSE,
        )

        responses.add(
            responses.GET,
            re.compile('.*/Line/.*/Status.*'),
            body=LINE_STATUS_RESPONSE,
        )

        responses.start()

    @classmethod
    def tearDownClass(cls):
        responses.stop()
