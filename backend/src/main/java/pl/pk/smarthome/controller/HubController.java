package pl.pk.smarthome.controller;

import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import pl.pk.smarthome.dto.HubStatusDto;
import pl.pk.smarthome.service.HubStatusService;

@RestController
@RequestMapping("/api/hub")
@RequiredArgsConstructor
public class HubController {

	private final HubStatusService hubStatusService;

	@GetMapping("/status")
	public HubStatusDto getStatus() {
		return hubStatusService.getStatus();
	}

}
