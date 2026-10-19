package pl.pk.smarthome.controller;

import java.util.List;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import pl.pk.smarthome.dto.DeviceCommandRequest;
import pl.pk.smarthome.dto.DeviceDto;
import pl.pk.smarthome.service.DeviceService;

@RestController
@RequestMapping("/api/devices")
@RequiredArgsConstructor
public class DeviceController {

	private final DeviceService deviceService;

	@GetMapping
	public List<DeviceDto> getAll() {
		return deviceService.getAll();
	}

	@GetMapping("/{code}")
	public DeviceDto getByCode(@PathVariable String code) {
		return deviceService.getByCode(code);
	}

	// 202: komenda wysłana, faktyczny stan przyjdzie z huba przez WebSocket
	@PostMapping("/{code}/command")
	@ResponseStatus(HttpStatus.ACCEPTED)
	public void sendCommand(@PathVariable String code, @Valid @RequestBody DeviceCommandRequest request) {
		deviceService.sendCommand(code, request.state());
	}

}
