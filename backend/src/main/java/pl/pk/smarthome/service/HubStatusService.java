package pl.pk.smarthome.service;

import java.time.Instant;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import pl.pk.smarthome.dto.HubStatusDto;
import pl.pk.smarthome.mqtt.message.HubStatusMessage;

// Status online/offline huba (retained + LWT), trzymany w pamięci
@Slf4j
@Service
@RequiredArgsConstructor
public class HubStatusService {

	private final LiveUpdateService liveUpdateService;

	// Do pierwszej wiadomości (retained przychodzi zaraz po subskrypcji) hub jest traktowany jako offline.
	private volatile HubStatusDto status = new HubStatusDto(false, null);

	public void handleStatus(HubStatusMessage message) {
		boolean online = "online".equalsIgnoreCase(message.state());
		if (!online && !"offline".equalsIgnoreCase(message.state())) {
			log.warn("Nieznany status huba: {}", message.state());
			return;
		}
		// LWT ("offline") nie ma znacznika czasu, wtedy liczy się czas odbioru.
		Instant since = message.ts() != null ? message.ts() : Instant.now();
		status = new HubStatusDto(online, since);
		log.info("Hub {}", online ? "online" : "offline");

		liveUpdateService.publish(LiveUpdateService.HUB, status);
	}

	public HubStatusDto getStatus() {
		return status;
	}

}
