package pl.pk.smarthome.dto;

import java.time.Instant;

import pl.pk.smarthome.entity.DeviceState;
import pl.pk.smarthome.entity.DeviceType;

public record DeviceDto(
		String code,
		String name,
		DeviceType type,
		DeviceState state,
		Instant stateUpdatedAt
) {
}
