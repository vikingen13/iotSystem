#this file contains the iot Events state machine

initial_state_name = "Initial"


def get_states(self):
    states = [
        {
            "stateName": "Initial",
            "onInput": {
                "events": [
                    {
                        "eventName": "CountInputs",
                        "condition": "true",
                        "actions": [
                            {
                                "setVariable": {
                                    "variableName": "input_message_count",
                                    "value": "$variable.input_message_count + 1"
                                }
                            }
                        ]
                    },
                    {
                        "eventName": "SetDeviceName",
                        "condition": "true",
                        "actions": [
                            {
                                "setVariable": {
                                    "variableName": "devicename",
                                    "value": "$input.esp8266simpletempsensorsConnectivityStatusInput.devicename"
                                }
                            }
                        ]
                    },
                    {
                        "eventName": "SetDeviceStatus",
                        "condition": "true",
                        "actions": [
                            {
                                "setVariable": {
                                    "variableName": "devicestatus",
                                    "value": "'connected'"
                                }
                            }
                        ]
                    }
                ],
                "transitionEvents": [
                    {
                        "eventName": "IsConnected",
                        "condition": "true",
                        "actions": [],
                        "nextState": "Connected"
                    }
                ]
            },
            "onEnter": {
                "events": [
                    {
                        "eventName": "Initialize",
                        "condition": "true",
                        "actions": [
                            {
                                "setVariable": {
                                    "variableName": "input_message_count",
                                    "value": "0"
                                }
                            }
                        ]
                    }
                ]
            },
            "onExit": {
                "events": []
            }
        },
        {
            "stateName": "Connected",
            "onInput": {
                "events": [
                    {
                        "eventName": "CollectInputMetricsAndRestartTimer",
                        "condition": "true",
                        "actions": [
                            {
                                "setVariable": {
                                    "variableName": "input_message_count",
                                    "value": "$variable.input_message_count + 1"
                                }
                            },
                            {
                                "setTimer": {
                                    "timerName": "DisconnectionTimer",
                                    "seconds": 1200,
                                }
                            }
                        ]
                    }
                ],
                "transitionEvents": [
                    {
                        "eventName": "DisconnectedTimerTimeout",
                        "condition": "timeout('DisconnectionTimer')",
                        "actions": [
                            {
                                "setVariable": {
                                    "variableName": "devicestatus",
                                    "value": "'disconnected'"
                                }
                            }

                        ],
                        "nextState": "Disconnected"
                    }
                ]
            },
            "onEnter": {
                "events": [
                    {
                        "eventName": "PublishPresenceMessage",
                        "condition": "true",
                        "actions": [
                            {
                                "sns": {
                                    "targetArn": "arn:aws:sns:" + self.region + ":" + self.account + ":esp8266simpletempsensorsNotificationTopic",
                                    "payload": {
                                        "contentExpression": "'RECONNECTED: Device ' + $variable.devicename + ' has established a connection'",
                                        "type": "STRING"
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "eventName": "SetTimer",
                        "condition": "true",
                        "actions": [
                            {
                                "setTimer": {
                                    "timerName": "DisconnectionTimer",
                                    "seconds": 600,
                                }
                            }
                        ]
                    }

                ]
            },
            "onExit": {
                "events": []
            }
        },
        {
            "stateName": "Disconnected",
            "onInput": {
                "events": [
                    {
                        "eventName": "CollectInputMetrics",
                        "condition": "true",
                        "actions": [
                            {
                                "setVariable": {
                                    "variableName": "input_message_count",
                                    "value": "$variable.input_message_count + 1"
                                }
                            },
                            {
                                "setVariable": {
                                    "variableName": "devicestatus",
                                    "value": "'connected'"
                                }
                            }
                        ]
                    }
                ],
                "transitionEvents": [
                    {
                        "eventName": "IsConnected",
                        "condition": "$variable.devicestatus == 'connected'",
                        "actions": [],
                        "nextState": "Connected"
                    }
                ]
            },
            "onEnter": {
                "events": [
                    {
                        "eventName": "Publish",
                        "condition": "true",
                        "actions": [
                            {
                                "sns": {
                                    "targetArn": "arn:aws:sns:" + self.region + ":" + self.account + ":esp8266simpletempsensorsNotificationTopic",
                                    "payload": {
                                        "contentExpression": "'DISCONNECTED: Device ' + $variable.devicename + ' is disconnected'",
                                        "type": "STRING"
                                    }
                                }
                            }
                        ]
                    }
                ]
            },
            "onExit": {
                "events": []
            }
        }
    ]

    return states