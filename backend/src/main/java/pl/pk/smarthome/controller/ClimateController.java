package pl.pk.smarthome.controller;

import java.time.Instant;
import java.util.List;

import lombok.RequiredArgsConstructor;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import pl.pk.smarthome.dto.ClimateReadingDto;
import pl.pk.smarthome.service.ClimateService;

@RestController
@RequestMapping("/api/climate")
@RequiredArgsConstructor
public class ClimateController {

	private final ClimateService climateService;

	@GetMapping("/latest")
	public ClimateReadingDto getLatest() {
		return climateService.getLatest();
	}

	@GetMapping("/history")
	public List<ClimateReadingDto> getHistory(
			@RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) Instant from,
			@RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) Instant to) {
		return climateService.getHistory(from, to);
	}

}
