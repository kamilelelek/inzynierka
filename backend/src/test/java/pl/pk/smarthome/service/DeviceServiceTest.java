package pl.pk.smarthome.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.time.Instant;
import java.util.Optional;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import pl.pk.smarthome.entity.Device;
import pl.pk.smarthome.entity.DeviceState;
import pl.pk.smarthome.entity.DeviceType;
import pl.pk.smarthome.mqtt.MqttCommandPublisher;
import pl.pk.smarthome.mqtt.message.DeviceStateMessage;
import pl.pk.smarthome.repository.DeviceRepository;
import pl.pk.smarthome.repository.DeviceStateChangeRepository;

class DeviceServiceTest {

	private static final Instant TS = Instant.parse("2026-10-19T12:00:00Z");

	private DeviceStateChangeRepository stateChangeRepository;
	private LiveUpdateService liveUpdateService;
	private DeviceService service;
	private Device led;

	@BeforeEach
	void setUp() {
		DeviceRepository deviceRepository = mock(DeviceRepository.class);
		stateChangeRepository = mock(DeviceStateChangeRepository.class);
		liveUpdateService = mock(LiveUpdateService.class);
		service = new DeviceService(deviceRepository, stateChangeRepository, mock(MqttCommandPublisher.class),
				liveUpdateService);

		led = new Device();
		led.setCode("led");
		led.setName("LED");
		led.setType(DeviceType.LIGHT);
		when(deviceRepository.findByCode("led")).thenReturn(Optional.of(led));
		when(deviceRepository.findByCode("fan")).thenReturn(Optional.empty());
	}

	@Test
	void historyOnlyOnChange() {
		service.handleStateReport("led", new DeviceStateMessage(DeviceState.ON, TS));
		service.handleStateReport("led", new DeviceStateMessage(DeviceState.ON, TS.plusSeconds(5)));

		assertThat(led.getState()).isEqualTo(DeviceState.ON);
		assertThat(led.getStateUpdatedAt()).isEqualTo(TS);
		verify(stateChangeRepository, times(1)).save(any());
		// Potwierdzenie idzie na dashboard za każdym razem.
		verify(liveUpdateService, times(2)).publish(eq(LiveUpdateService.DEVICES), any());
	}

	@Test
	void unknownDeviceIsIgnored() {
		service.handleStateReport("fan", new DeviceStateMessage(DeviceState.ON, TS));

		verify(stateChangeRepository, never()).save(any());
		verify(liveUpdateService, never()).publish(any(), any());
	}

}
