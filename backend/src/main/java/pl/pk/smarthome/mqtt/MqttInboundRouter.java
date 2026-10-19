package pl.pk.smarthome.mqtt;

import lombok.RequiredArgsConstructor;
import org.springframework.messaging.Message;
import org.springframework.stereotype.Component;
import pl.pk.smarthome.service.ClimateService;
import pl.pk.smarthome.service.DeviceService;
import pl.pk.smarthome.service.HubStatusService;
import pl.pk.smarthome.service.MotionService;

// Odbiera wiadomości z huba i przekazuje je do serwisów
@Component
@RequiredArgsConstructor
public class MqttInboundRouter {

	private final MqttTopics topics;
	private final ClimateService climateService;
	private final MotionService motionService;
	private final DeviceService deviceService;
	private final HubStatusService hubStatusService;

	// TODO: @ServiceActivator(inputChannel = "mqttInboundChannel")
	public void handle(Message<String> message) {
		// TODO: topic z nagłówka MqttHeaders.RECEIVED_TOPIC, JSON -> rekord z pakietu mqtt.message,
		//  potem wywołanie odpowiedniego serwisu
	}

}
