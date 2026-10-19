package pl.pk.smarthome.service;

import java.util.List;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import pl.pk.smarthome.dto.MotionEventDto;
import pl.pk.smarthome.mqtt.message.MotionEventMessage;
import pl.pk.smarthome.repository.MotionEventRepository;

@Service
@RequiredArgsConstructor
public class MotionService {

	private final MotionEventRepository eventRepository;
	private final LiveUpdateService liveUpdateService;

	public void handleEvent(MotionEventMessage message) {
		// TODO: zapis zdarzenia, push na WebSocket
	}

	public List<MotionEventDto> getRecent(int limit) {
		throw new UnsupportedOperationException("TODO");
	}

}
