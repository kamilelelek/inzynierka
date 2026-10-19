package pl.pk.smarthome.dto;

import java.time.Instant;

public record MotionEventDto(
		boolean motion,
		Instant detectedAt
) {
}
