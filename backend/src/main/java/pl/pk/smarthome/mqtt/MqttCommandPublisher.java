package pl.pk.smarthome.mqtt;

import org.springframework.stereotype.Component;
import pl.pk.smarthome.mqtt.message.DeviceCommandMessage;

// Wysyła komendy do huba (topic .../set, QoS 1)
@Component
public class MqttCommandPublisher {

	public void publishCommand(String deviceCode, DeviceCommandMessage command) {
		// TODO: serializacja do JSON i wysłanie na mqttOutboundChannel z nagłówkiem MqttHeaders.TOPIC
	}

}
