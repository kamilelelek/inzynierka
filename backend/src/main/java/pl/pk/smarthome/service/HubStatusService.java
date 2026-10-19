package pl.pk.smarthome.service;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import pl.pk.smarthome.dto.HubStatusDto;
import pl.pk.smarthome.mqtt.message.HubStatusMessage;

// Status online/offline huba (retained + LWT), trzymany w pamięci
@Service
@RequiredArgsConstructor
public class HubStatusService {

	private final LiveUpdateService liveUpdateService;

	public void handleStatus(HubStatusMessage message) {
		// TODO: zapamiętać status i czas zmiany, push na WebSocket
	}

	public HubStatusDto getStatus() {
		throw new UnsupportedOperationException("TODO");
	}

}
