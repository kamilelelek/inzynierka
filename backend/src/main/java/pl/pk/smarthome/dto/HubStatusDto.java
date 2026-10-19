package pl.pk.smarthome.dto;

import java.time.Instant;

public record HubStatusDto(
		boolean online,
		Instant since
) {
}
