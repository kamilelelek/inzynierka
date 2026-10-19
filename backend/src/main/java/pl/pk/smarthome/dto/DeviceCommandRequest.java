package pl.pk.smarthome.dto;

import jakarta.validation.constraints.NotNull;
import pl.pk.smarthome.entity.DeviceState;

public record DeviceCommandRequest(
		@NotNull DeviceState state
) {
}
