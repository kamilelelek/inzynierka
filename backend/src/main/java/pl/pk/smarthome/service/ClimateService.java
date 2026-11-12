package pl.pk.smarthome.service;

import java.time.Instant;
import java.util.List;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import pl.pk.smarthome.dto.ClimateReadingDto;
import pl.pk.smarthome.entity.ClimateReading;
import pl.pk.smarthome.mqtt.message.ClimateTelemetryMessage;
import pl.pk.smarthome.repository.ClimateReadingRepository;

@Slf4j
@Service
@RequiredArgsConstructor
public class ClimateService {

	private final ClimateReadingRepository readingRepository;
	private final ThermostatService thermostatService;
	private final LiveUpdateService liveUpdateService;

	public void handleTelemetry(ClimateTelemetryMessage message) {
		if (message.temperature() == null || message.humidity() == null) {
			log.warn("Odczyt bez temperatury lub wilgotności, pomijam: {}", message);
			return;
		}

		ClimateReading reading = new ClimateReading();
		reading.setTemperature(message.temperature());
		reading.setHumidity(message.humidity());
		// Czas pomiaru z huba; gdyby go zabrakło, czas odbioru.
		reading.setMeasuredAt(message.ts() != null ? message.ts() : Instant.now());
		readingRepository.save(reading);

		liveUpdateService.publish(LiveUpdateService.CLIMATE, toDto(reading));
		thermostatService.onTemperature(reading.getTemperature());
	}

	public ClimateReadingDto getLatest() {
		throw new UnsupportedOperationException("TODO");
	}

	public List<ClimateReadingDto> getHistory(Instant from, Instant to) {
		throw new UnsupportedOperationException("TODO");
	}

	private static ClimateReadingDto toDto(ClimateReading reading) {
		return new ClimateReadingDto(reading.getTemperature(), reading.getHumidity(), reading.getMeasuredAt());
	}

}
