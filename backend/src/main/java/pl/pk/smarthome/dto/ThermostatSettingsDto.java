package pl.pk.smarthome.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;

public record ThermostatSettingsDto(
		boolean enabled,
		@NotNull Double targetTemperature,
		@NotNull @Positive Double hysteresis
) {
}
