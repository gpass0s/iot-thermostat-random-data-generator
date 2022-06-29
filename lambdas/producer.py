#!/usr/bin/python3.8
# -*- encoding: utf-8 -*-
"""
Created on Tue Jun 28 08:04 BRT 2022
Updated on Tue Jun 28 08:04 BRT 2022
author: https://github.com/gpass0s/
This module implements a fake data producer for the IoT process
"""
import boto3
import json
import os
import threading
import time
import uuid
import random
import datetime

_kds_client = boto3.client('kinesis')
_kds_name = os.environ["KDS_NAME"]
_kds_partitions = int(os.environ["KDS_PARTITIONS"])
aws_region = os.environ["REGION"]


def generate_temperature_message(
        iot_id: str,
        trace_id: str,
        span_id: str,
        temperature_trend: int,
        current_temperature: int,
        humidity_trend: int,
        current_humidity: int,
) -> tuple:
    temperature_delta_dist = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.08, 0.09, 0.11, 0.12, 0.13, 0.14, 0.20, 0.21,
                              0.22, 0.23, 0.25, 0.31]
    temperature_delta = temperature_delta_dist[random.randint(0, len(temperature_delta_dist) - 1)]
    temperature = current_temperature + temperature_trend * temperature_delta

    humidity_delta_dist = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 2, 2, 2, 3, 3, 3]
    humidity_delta = humidity_delta_dist[random.randint(0, len(humidity_delta_dist) - 1)]
    humidity = current_humidity + humidity_trend * humidity_delta

    event = {
        "time": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3],
        "level": "DEBUG",
        "traceId": trace_id,
        "spanId": span_id,
        "requestId": "",
        "applicationId": "",
        "source": "c.f3wireless.thermogate.listeners.UpstreamRequestEventListener:97",
        "message": f"[Upstream|CHUNK]({iot_id}:---): Command TemperatureHumidity(roomTemperature={temperature}, " +
                   f"humidity={humidity}, measuredTemperature={temperature})"
    }

    return event, temperature, humidity


def generate_power_status_message(
        iot_id: str,
        trace_id: str,
        span_id: str,
        current_battery_voltage: int
) -> tuple:
    voltage_delta_dist = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.1, 0.1]
    voltage_delta = voltage_delta_dist[random.randint(0, len(voltage_delta_dist) - 1)]
    battery_voltage = current_battery_voltage - voltage_delta

    event = {
        "time": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3],
        "level": "DEBUG",
        "traceId": trace_id,
        "spanId": span_id,
        "requestId": "",
        "applicationId": "",
        "source": "c.f3wireless.thermogate.listeners.UpstreamRequestEventListener:125",
        "message": f"[Upstream|CHUNK]({iot_id}:---): Command PowerStatus(systemVoltage=24, " +
                   f"batteryVoltage={battery_voltage})"
    }

    return event, battery_voltage


def generate_relay_position_message(
        iot_id: str,
        trace_id: str,
        span_id: str,
        relay_position: int
) -> dict:
    event = {
        "time": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3],
        "level": "DEBUG",
        "traceId": trace_id,
        "spanId": span_id,
        "requestId": "",
        "applicationId": "",
        "source": "c.f3wireless.thermogate.listeners.UpstreamRequestEventListener:125",
        "message": f"[Upstream|CHUNK]({iot_id}:---): Command RelayPosition(relayPosition={relay_position})"
    }

    return event


def threads_controller():
    iot_id = random.getrandbits(64)
    curr_temp = random.randint(30, 80)
    curr_humidity = random.randint(35, 50)
    curr_battery_voltage = 3.2
    trend_change = random.randint(30, 200)
    trend = [-1, 1]
    relay_position = random.randint(0, 6)
    count = 0
    while count < 100:

        if count == 0 or count % trend_change == 0:
            humidity_trend = trend[random.randint(0, 1)]
            temperature_trend = trend[random.randint(0, 1)]

        span_id = uuid.uuid4().hex
        trace_id = uuid.uuid4().hex

        power_message, curr_battery_voltage = generate_power_status_message(
            iot_id=iot_id,
            trace_id=trace_id,
            span_id=span_id,
            current_battery_voltage=curr_battery_voltage
        )

        temperature_message, curr_temp, curr_humidity = generate_temperature_message(
            iot_id=iot_id,
            trace_id=trace_id,
            span_id=span_id,
            temperature_trend=temperature_trend,
            current_temperature=curr_temp,
            humidity_trend=humidity_trend,
            current_humidity=curr_humidity
        )

        relay_message = generate_relay_position_message(
            iot_id=iot_id,
            trace_id=trace_id,
            span_id=span_id,
            relay_position=relay_position
        )

        messages = [power_message, temperature_message, relay_message]

        for message in messages:
            _kds_client.put_record(StreamName=_kds_name,
                                   Data=json.dumps(message),
                                   PartitionKey=str(random.randint(1, _kds_partitions))
                                   )

            print(f"MESSAGE FROM {iot_id} DEVICE SUCCESSFULLY SENT TO KDS: {json.dumps(message)}")
        count += 1
        time.sleep(random.uniform(5, 15))


def lambda_handler(event, context):
    """
        Lambda method that is invoked by SQS
        :param event: message from SQS
        :param context:
    """

    number_of_threads = int(os.environ["NUMBER_OF_THREADS"]) # threads simulate concurrent accesses

    print("[INFO] Starting data producer")

    threads = []

    print("[INFO] Starting parallel threads")
    for i in range(number_of_threads):  # start threads
        thread = threading.Thread(target=threads_controller)
        thread.start()
        print(f"[INFO] Thread {i} started")
        threads.append(thread)

    for thread in threads:
        thread.join()
