package pl.pk.smarthome.service;

import java.time.Instant;
import java.util.List;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import pl.pk.smarthome.dto.MotionEventDto;
import pl.pk.smarthome.entity.MotionEvent;
import pl.pk.smarthome.mqtt.message.MotionEventMessage;
import pl.pk.smarthome.repository.MotionEventRepository;

@Service
@RequiredArgsConstructor
public class MotionService {

	private final MotionEventRepository eventRepository;
	private final LiveUpdateService liveUpdateService;

	// Hub wysyła motion=true na początku ruchu i motion=false po jego końcu (po debounce).
	public void handleEvent(MotionEventMessage message) {
		MotionEvent event = new MotionEvent();
		event.setMotion(message.motion());
		event.setDetectedAt(message.ts() != null ? message.ts() : Instant.now());
		eventRepository.save(event);

		liveUpdateService.publish(LiveUpdateService.MOTION, toDto(event));
	}

	public List<MotionEventDto> getRecent(int limit) {
		throw new UnsupportedOperationException("TODO");
	}

	private static MotionEventDto toDto(MotionEvent event) {
		return new MotionEventDto(event.isMotion(), event.getDetectedAt());
	}

}
