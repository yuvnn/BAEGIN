package com.baegin.auth.controller;

import com.baegin.auth.dto.LoginRequest;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Base64;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class AuthController {

    @GetMapping("/health")
    public Map<String, String> health() {
        Map<String, String> response = new LinkedHashMap<>();
        response.put("status", "ok");
        response.put("service", "auth-server");
        return response;
    }

    @PostMapping("/auth/login")
    public Map<String, String> login(@RequestBody LoginRequest payload) {
        String username = payload.username() == null ? "anonymous" : payload.username();
        String raw = username + ":" + Instant.now().toEpochMilli() + ":" + UUID.randomUUID();
        String token = Base64.getUrlEncoder().withoutPadding().encodeToString(raw.getBytes(StandardCharsets.UTF_8));

        Map<String, String> response = new LinkedHashMap<>();
        response.put("access_token", token);
        response.put("token_type", "bearer");
        return response;
    }
}
