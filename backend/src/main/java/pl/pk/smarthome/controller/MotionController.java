package pl.pk.smarthome.controller;

import java.util.List;

import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import pl.pk.smarthome.dto.MotionEventDto;
import pl.pk.smarthome.service.MotionService;

@RestController
@RequestMapping("/api/motion")
@RequiredArgsConstructor
public class MotionController {

	private final MotionService motionService;

	@GetMapping("/events")
	public List<MotionEventDto> getRecent(@RequestParam(defaultValue = "50") int limit) {
		return motionService.getRecent(limit);
	}

}
