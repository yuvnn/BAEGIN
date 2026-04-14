package com.baegin.auth.service;

import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.stereotype.Service;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.List;

@Service
public class JwtService {

    private final SecretKey key;

    public JwtService() {
        String secret = System.getenv("JWT_SECRET");
        if (secret == null || secret.length() < 32) {
            secret = "default-dev-secret-at-least-32-chars!!";
        }
        this.key = Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
    }

    public String generateToken(String email, String userId, String name, List<String> keywords) {
        long now = System.currentTimeMillis();
        String keywordsStr = keywords == null ? "" : String.join(",", keywords);

        return Jwts.builder()
                .subject(email)
                .claim("user_id", userId)
                .claim("email", email)
                .claim("name", name)
                .claim("keywords", keywordsStr)
                .issuedAt(new Date(now))
                .expiration(new Date(now + 24 * 60 * 60 * 1000L))
                .signWith(key)
                .compact();
    }
}
