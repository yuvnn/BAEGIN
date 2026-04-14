package com.baegin.auth.controller;

import com.baegin.auth.dto.LoginRequest;
import com.baegin.auth.dto.OtpSendRequest;
import com.baegin.auth.dto.RegisterRequest;
import com.baegin.auth.service.JwtService;
import com.baegin.auth.service.OtpStore;
import com.baegin.auth.service.SlackService;
import com.baegin.auth.service.UserStore;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.LinkedHashMap;
import java.util.Map;

@RestController
public class AuthController {

    private final JwtService jwtService;
    private final OtpStore otpStore;
    private final SlackService slackService;
    private final UserStore userStore;

    public AuthController(JwtService jwtService, OtpStore otpStore,
                          SlackService slackService, UserStore userStore) {
        this.jwtService = jwtService;
        this.otpStore = otpStore;
        this.slackService = slackService;
        this.userStore = userStore;
    }

    @GetMapping("/health")
    public Map<String, String> health() {
        return Map.of("status", "ok", "service", "auth-server");
    }

    @PostMapping("/auth/otp/send")
    public ResponseEntity<Map<String, String>> sendOtp(@RequestBody OtpSendRequest req) {
        if (req.email() == null || req.email().isBlank()) {
            return ResponseEntity.badRequest().body(Map.of("error", "email required"));
        }
        String code = otpStore.save(req.email());
        slackService.sendOtp(req.email(), code);
        return ResponseEntity.ok(Map.of("message", "OTP sent"));
    }

    @PostMapping("/auth/register")
    public ResponseEntity<Map<String, Object>> register(@RequestBody RegisterRequest req) {
        if (!otpStore.verify(req.email(), req.otp())) {
            return ResponseEntity.status(401).body(Map.of("error", "invalid or expired OTP"));
        }
        UserStore.UserRecord user;
        try {
            user = userStore.register(req.email(), req.name(), req.keywords(), req.password());
        } catch (IllegalStateException e) {
            return ResponseEntity.status(409).body(Map.of("error", "이미 가입된 이메일입니다."));
        }
        String token = jwtService.generateToken(user.email(), user.userId(), user.name(), user.keywords());

        Map<String, Object> resp = new LinkedHashMap<>();
        resp.put("access_token", token);
        resp.put("token_type", "bearer");
        resp.put("user", Map.of(
                "email", user.email(),
                "name", user.name(),
                "keywords", user.keywords()
        ));
        return ResponseEntity.ok(resp);
    }

    @PostMapping("/auth/login")
    public ResponseEntity<Map<String, Object>> login(@RequestBody LoginRequest req) {
        if (req.email() == null || req.email().isBlank() || req.password() == null || req.password().isBlank()) {
            return ResponseEntity.badRequest().body(Map.of("error", "email and password required"));
        }
        UserStore.UserRecord user = userStore.find(req.email());
        if (user == null) {
            return ResponseEntity.status(401).body(Map.of("error", "가입되지 않은 이메일입니다."));
        }
        if (!userStore.verifyPassword(req.email(), req.password())) {
            return ResponseEntity.status(401).body(Map.of("error", "비밀번호가 올바르지 않습니다."));
        }
        String token = jwtService.generateToken(user.email(), user.userId(), user.name(), user.keywords());

        Map<String, Object> resp = new LinkedHashMap<>();
        resp.put("access_token", token);
        resp.put("token_type", "bearer");
        resp.put("user", Map.of(
                "email", user.email(),
                "name", user.name(),
                "keywords", user.keywords()
        ));
        return ResponseEntity.ok(resp);
    }
}
