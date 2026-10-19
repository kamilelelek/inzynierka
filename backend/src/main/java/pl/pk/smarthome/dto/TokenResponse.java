package pl.pk.smarthome.dto;

import java.time.Instant;

public record TokenResponse(
		String accessToken,
		Instant expiresAt
) {
}
