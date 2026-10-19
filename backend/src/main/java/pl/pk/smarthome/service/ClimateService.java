package pl.pk.smarthome.service;

import java.time.Instant;
import java.util.List;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import pl.pk.smarthome.dto.ClimateReadingDto;
import pl.pk.smarthome.mqtt.message.ClimateTelemetryMessage;
import pl.pk.smarthome.repository.ClimateReadingRepository;

@Service
@RequiredArgsConstructor
public class ClimateService {

	private final ClimateReadingRepository readingRepository;
	private final ThermostatService thermostatService;
	private final LiveUpdateService liveUpdateService;

	public void handleTelemetry(ClimateTelemetryMessage message) {
		// TODO: zapis odczytu, push na WebSocket, przekazanie temperatury do termostatu
	}

	public ClimateReadingDto getLatest() {
		throw new UnsupportedOperationException("TODO");
	}

	public List<ClimateReadingDto> getHistory(Instant from, Instant to) {
		throw new UnsupportedOperationException("TODO");
	}

}
