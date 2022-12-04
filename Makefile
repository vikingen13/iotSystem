REGION=eu-west-1 
CREATECERT = aws iot create-keys-and-certificate \
                --set-as-active \
                --certificate-pem-outfile $(name).certificate.pem \
                --public-key-outfile $(name).public_key.pem \
                --private-key-outfile $(name).private_key.pem | jq -r .certificateArn
RETRIEVECERT = aws iot list-thing-principals --thing-name $(name) | jq -r .principals[0]
ENDPOINT = aws iot describe-endpoint --endpoint-type iot:Data-ATS |jq -r .endpointAddress

all: esp8266TempSensorType allInfra

allInfra: 
	source .venv/bin/activate; \
	cdk deploy --all --parameters timeStreamDBName=$(dbName)

esp8266TempSensor: esp8266TempSensorType esp8266InfraOnly

esp8266TempSensorType:
	aws iot create-thing-type --thing-type-name "esp8266_temperature_sensor" --thing-type-properties thingTypeDescription="Temperature sensors built with esp8266"

esp8266InfraOnly:
	source .venv/bin/activate; \
	cdk deploy esp8266tempsensors --parameters timeStreamDBName=$(dbName)

esp8266TempSensorCreate:
	echo "creating sensor"
	@aws iot create-thing --thing-name $(name) --thing-type-name esp8266_temperature_sensor
	echo "sensor created"
	
	echo "creating certificate with the right policy and attach it to the sensor"
	@cd certificates;mkdir $(name);cd $(name); \
	CERTARN=$$($(CREATECERT)); \
	aws iot attach-thing-principal --principal $$CERTARN --thing-name $(name); \
	aws iot attach-policy --target $$CERTARN --policy-name esp8266tempsensors-policy
	echo "certificate created"

	echo "create the esp8266 code package"
	cd esp8266tempsensors/sensors/; \
	mkdir $(name); cd $(name); \
	cp ../../../certificates/$(name)/* ./; \
	openssl rsa -in $(name).private_key.pem -out key -outform DER ; \
	openssl x509 -in $(name).certificate.pem -out cert -outform DER ; \
	cp ../../code/main.py ./ ; \
	sed -i -e "s/PUT_THING_NAME_HERE/$(name)/g" main.py; \
	 \
	sed -i -e "s/PUT_MQTT_HOST_HERE/$$($(ENDPOINT))/g" main.py; \
	sed -i -e "s/PUT_WIFI_SSID_HERE/$(wifissid)/g" main.py; \
	sed -i -e "s/PUT_WIFI_PASSWORD_HERE/$(wifipassword)/g" main.py; \
	rm *.pem
	echo "code package created"

	echo "creation ok"

esp8266TempSensorDelete:
	@echo "detaching the certificate from the thing and the policy"
	CERTARN=$$($(RETRIEVECERT)); \
	CERTID=$$(echo $$CERTARN|rev|cut -d/ -f1|rev); \
	aws iot detach-policy --target $$CERTARN --policy-name esp8266tempsensors-policy ; \
	aws iot detach-thing-principal --principal $$CERTARN --thing-name $(name); \
	aws iot update-certificate --certificate-id  $$CERTID --new-status INACTIVE; \
	aws iot delete-certificate --certificate-id $$CERTID
	echo "all is done for certificate"
	echo "remove the sensor"
	@aws iot delete-thing --thing-name $(name)
	echo "sensor removed"
	echo "remove artifacts"
	cd certificates; rm -r $(name)
	cd esp8266tempsensors/sensors; rm -r $(name)
	echo "sensor removed"
