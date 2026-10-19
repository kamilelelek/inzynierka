package pl.pk.smarthome.dto;

import java.time.Instant;

public record ClimateReadingDto(
		Double temperature,
		Double humidity,
		Instant measuredAt
) {
}
