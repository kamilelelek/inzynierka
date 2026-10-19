package pl.pk.smarthome.mqtt.message;

import java.time.Instant;

// home/<hubId>/status: "online" / "offline" (LWT, bez ts)
public record HubStatusMessage(
		String state,
		Instant ts
) {
}
