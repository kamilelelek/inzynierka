package pl.pk.smarthome.mqtt;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;

import java.time.Instant;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.integration.mqtt.support.MqttHeaders;
import org.springframework.integration.support.MessageBuilder;
import pl.pk.smarthome.config.MqttProperties;
import pl.pk.smarthome.entity.DeviceState;
import pl.pk.smarthome.mqtt.message.ClimateTelemetryMessage;
import pl.pk.smarthome.mqtt.message.DeviceStateMessage;
import pl.pk.smarthome.mqtt.message.HubStatusMessage;
import pl.pk.smarthome.mqtt.message.MotionEventMessage;
import pl.pk.smarthome.service.ClimateService;
import pl.pk.smarthome.service.DeviceService;
import pl.pk.smarthome.service.HubStatusService;
import pl.pk.smarthome.service.MotionService;
import tools.jackson.databind.json.JsonMapper;

class MqttInboundRouterTest {

	private ClimateService climateService;
	private MotionService motionService;
	private DeviceService deviceService;
	private HubStatusService hubStatusService;
	private MqttInboundRouter router;

	@BeforeEach
	void setUp() {
		climateService = mock(ClimateService.class);
		motionService = mock(MotionService.class);
		deviceService = mock(DeviceService.class);
		hubStatusService = mock(HubStatusService.class);
		MqttTopics topics = new MqttTopics(new MqttProperties("tcp://localhost:1883", "test", null, null, "hub1"));
		router = new MqttInboundRouter(topics, JsonMapper.builder().build(),
				climateService, motionService, deviceService, hubStatusService);
	}

	private void receive(String topic, String payload) {
		router.handle(MessageBuilder.withPayload(payload).setHeader(MqttHeaders.RECEIVED_TOPIC, topic).build());
	}

	@Test
	void climateTelemetry() {
		receive("home/hub1/climate/telemetry", "{\"temperature\":21.4,\"humidity\":45.2,\"ts\":\"2026-10-19T12:00:00Z\"}");

		ArgumentCaptor<ClimateTelemetryMessage> captor = ArgumentCaptor.forClass(ClimateTelemetryMessage.class);
		verify(climateService).handleTelemetry(captor.capture());
		assertThat(captor.getValue()).isEqualTo(
				new ClimateTelemetryMessage(21.4, 45.2, Instant.parse("2026-10-19T12:00:00Z")));
	}

	@Test
	void motionEvent() {
		receive("home/hub1/motion/event", "{\"motion\":true,\"ts\":\"2026-10-19T12:00:00Z\"}");

		verify(motionService).handleEvent(new MotionEventMessage(true, Instant.parse("2026-10-19T12:00:00Z")));
	}

	@Test
	void lastWillWithoutTimestamp() {
		receive("home/hub1/status", "{\"state\":\"offline\"}");

		verify(hubStatusService).handleStatus(new HubStatusMessage("offline", null));
	}

	@Test
	void deviceStateReport() {
		receive("home/hub1/heater/state", "{\"state\":\"ON\",\"ts\":\"2026-10-19T12:00:00Z\"}");

		verify(deviceService).handleStateReport("heater",
				new DeviceStateMessage(DeviceState.ON, Instant.parse("2026-10-19T12:00:00Z")));
	}

	@Test
	void ownCommandsAndOtherHubsAreIgnored() {
		receive("home/hub1/led/set", "{\"state\":\"ON\"}");
		receive("home/hub2/led/state", "{\"state\":\"ON\"}");

		verifyNoInteractions(climateService, motionService, deviceService, hubStatusService);
	}

	@Test
	void invalidJsonDoesNotThrow() {
		receive("home/hub1/climate/telemetry", "not json");
		receive("home/hub1/led/state", "{\"state\":\"MAYBE\"}");

		verify(climateService, never()).handleTelemetry(any());
		verify(deviceService, never()).handleStateReport(anyString(), any());
	}

}
