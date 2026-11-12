package pl.pk.smarthome.service;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import pl.pk.smarthome.dto.DeviceDto;
import pl.pk.smarthome.entity.Device;
import pl.pk.smarthome.entity.DeviceState;
import pl.pk.smarthome.entity.DeviceStateChange;
import pl.pk.smarthome.mqtt.MqttCommandPublisher;
import pl.pk.smarthome.mqtt.message.DeviceStateMessage;
import pl.pk.smarthome.repository.DeviceRepository;
import pl.pk.smarthome.repository.DeviceStateChangeRepository;

@Slf4j
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

	// Hub publikuje stan po każdej komendzie i po każdym połączeniu z brokerem, także bez zmiany,
	// więc historia dostaje wpis tylko przy faktycznej zmianie stanu.
	@Transactional
	public void handleStateReport(String code, DeviceStateMessage message) {
		if (message.state() == null) {
			log.warn("Raport stanu {} bez pola state, pomijam", code);
			return;
		}
		Optional<Device> found = deviceRepository.findByCode(code);
		if (found.isEmpty()) {
			log.warn("Raport stanu nieznanego urządzenia: {}", code);
			return;
		}

		Device device = found.get();
		Instant reportedAt = message.ts() != null ? message.ts() : Instant.now();
		if (device.getState() != message.state()) {
			device.setState(message.state());
			device.setStateUpdatedAt(reportedAt);

			DeviceStateChange change = new DeviceStateChange();
			change.setDevice(device);
			change.setState(message.state());
			change.setChangedAt(reportedAt);
			stateChangeRepository.save(change);
			log.info("Urządzenie {}: {}", code, message.state());
		}

		// Push także bez zmiany: dashboard dostaje potwierdzenie wysłanej komendy.
		liveUpdateService.publish(LiveUpdateService.DEVICES, toDto(device));
	}

	private static DeviceDto toDto(Device device) {
		return new DeviceDto(device.getCode(), device.getName(), device.getType(), device.getState(),
				device.getStateUpdatedAt());
	}

}
