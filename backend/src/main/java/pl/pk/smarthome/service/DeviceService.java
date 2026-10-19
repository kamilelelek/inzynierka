package pl.pk.smarthome.service;

import java.util.List;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import pl.pk.smarthome.dto.DeviceDto;
import pl.pk.smarthome.entity.DeviceState;
import pl.pk.smarthome.mqtt.MqttCommandPublisher;
import pl.pk.smarthome.mqtt.message.DeviceStateMessage;
import pl.pk.smarthome.repository.DeviceRepository;
import pl.pk.smarthome.repository.DeviceStateChangeRepository;

@Service
@RequiredArgsConstructor
public class DeviceService {

	private final DeviceRepository deviceRepository;
	private final DeviceStateChangeRepository stateChangeRepository;
	private final MqttCommandPublisher commandPublisher;
	private final LiveUpdateService liveUpdateService;

	public List<DeviceDto> getAll() {
		throw new UnsupportedOperationException("TODO");
	}

	public DeviceDto getByCode(String code) {
		throw new UnsupportedOperationException("TODO");
	}

	public void sendCommand(String code, DeviceState state) {
		// TODO: sprawdzić, czy urządzenie istnieje, i wysłać komendę przez MQTT.
		//  Stan w bazie zmienia dopiero potwierdzenie z huba (handleStateReport).
	}

	public void handleStateReport(String code, DeviceStateMessage message) {
		// TODO: aktualizacja Device.state, wpis DeviceStateChange, push na WebSocket
	}

}
