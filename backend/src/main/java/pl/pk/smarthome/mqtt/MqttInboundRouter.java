package pl.pk.smarthome.mqtt;

import java.util.Optional;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.integration.annotation.ServiceActivator;
import org.springframework.integration.mqtt.support.MqttHeaders;
import org.springframework.messaging.Message;
import org.springframework.stereotype.Component;
import pl.pk.smarthome.mqtt.message.ClimateTelemetryMessage;
import pl.pk.smarthome.mqtt.message.DeviceStateMessage;
import pl.pk.smarthome.mqtt.message.HubStatusMessage;
import pl.pk.smarthome.mqtt.message.MotionEventMessage;
import pl.pk.smarthome.service.ClimateService;
import pl.pk.smarthome.service.DeviceService;
import pl.pk.smarthome.service.HubStatusService;
import pl.pk.smarthome.service.MotionService;
import tools.jackson.core.JacksonException;
import tools.jackson.databind.json.JsonMapper;

// Odbiera wiadomości z huba i przekazuje je do serwisów
@Slf4j
@Component
@RequiredArgsConstructor
public class MqttInboundRouter {

	private final MqttTopics topics;
	private final JsonMapper jsonMapper;
	private final ClimateService climateService;
	private final MotionService motionService;
	private final DeviceService deviceService;
	private final HubStatusService hubStatusService;

	@ServiceActivator(inputChannel = "mqttInboundChannel")
	public void handle(Message<String> message) {
		String topic = message.getHeaders().get(MqttHeaders.RECEIVED_TOPIC, String.class);
		if (topic == null) {
			return;
		}
		String payload = message.getPayload();
		log.debug("<- {} {}", topic, payload);

		// Błędna wiadomość nie może przerwać odbioru kolejnych, więc wyjątki kończą się na logu.
		try {
			route(topic, payload);
		} catch (JacksonException e) {
			log.warn("Niepoprawny JSON na {}: {} ({})", topic, payload, e.getOriginalMessage());
		} catch (RuntimeException e) {
			log.error("Błąd obsługi wiadomości z {}", topic, e);
		}
	}

	private void route(String topic, String payload) {
		if (topic.equals(topics.climateTelemetry())) {
			climateService.handleTelemetry(jsonMapper.readValue(payload, ClimateTelemetryMessage.class));
		} else if (topic.equals(topics.motionEvent())) {
			motionService.handleEvent(jsonMapper.readValue(payload, MotionEventMessage.class));
		} else if (topic.equals(topics.status())) {
			hubStatusService.handleStatus(jsonMapper.readValue(payload, HubStatusMessage.class));
		} else {
			Optional<String> deviceCode = topics.deviceCodeFromStateTopic(topic);
			if (deviceCode.isPresent()) {
				deviceService.handleStateReport(deviceCode.get(), jsonMapper.readValue(payload, DeviceStateMessage.class));
			}
			// Pozostałe topiki (np. komendy .../set wracające z subskrypcji #) są pomijane.
		}
	}

}
