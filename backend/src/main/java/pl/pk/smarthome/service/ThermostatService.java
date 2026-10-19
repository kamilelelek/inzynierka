package pl.pk.smarthome.service;

import lombok.RequiredArgsConstructor;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import pl.pk.smarthome.dto.ThermostatSettingsDto;
import pl.pk.smarthome.repository.ThermostatSettingsRepository;

// Regulacja z histerezą. Otwarta decyzja: logika tutaj czy na Pi (patrz CLAUDE.md).
@Service
@RequiredArgsConstructor
public class ThermostatService {

	private final ThermostatSettingsRepository settingsRepository;
	private final DeviceService deviceService;

	public ThermostatSettingsDto getSettings() {
		throw new UnsupportedOperationException("TODO");
	}

	public ThermostatSettingsDto updateSettings(ThermostatSettingsDto settings) {
		throw new UnsupportedOperationException("TODO");
	}

	public void onTemperature(double temperature) {
		// TODO: ON poniżej (target - hysteresis/2), OFF powyżej (target + hysteresis/2)
	}

	// Heartbeat dla fail-safe na Pi: grzałka gaśnie, jeśli komenda nie przyjdzie przez HEATER_COMMAND_TIMEOUT_S
	@Scheduled(fixedDelayString = "${smarthome.heater.command-refresh-ms}")
	public void refreshHeaterCommand() {
		// TODO: jeśli grzałka ma być włączona, ponownie wysłać heater/set ON
	}

}
