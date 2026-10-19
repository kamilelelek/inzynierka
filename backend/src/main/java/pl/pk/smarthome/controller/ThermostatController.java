package pl.pk.smarthome.controller;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import pl.pk.smarthome.dto.ThermostatSettingsDto;
import pl.pk.smarthome.service.ThermostatService;

@RestController
@RequestMapping("/api/thermostat")
@RequiredArgsConstructor
public class ThermostatController {

	private final ThermostatService thermostatService;

	@GetMapping
	public ThermostatSettingsDto getSettings() {
		return thermostatService.getSettings();
	}

	@PutMapping
	public ThermostatSettingsDto updateSettings(@Valid @RequestBody ThermostatSettingsDto settings) {
		return thermostatService.updateSettings(settings);
	}

}
