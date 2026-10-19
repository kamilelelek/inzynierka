package pl.pk.smarthome.mqtt.message;

import java.time.Instant;

// home/<hubId>/motion/event
public record MotionEventMessage(
		boolean motion,
		Instant ts
) {
}
