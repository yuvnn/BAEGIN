package com.lecture.gateway.filter;

import lombok.extern.slf4j.Slf4j;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.security.core.context.ReactiveSecurityContextHolder;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationToken;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

/**
 * JWT 토큰의 클레임 정보를 하위 서비스로 전달하는 글로벌 필터
 * - X-User-Id, X-User-Email, X-User-Role 헤더 추가
 * - 각 서비스는 이 헤더를 통해 인증된 사용자 정보 사용
 *
 * 우선순위
 * 1) X-User-Id   : user_id -> id -> sub
 * 2) X-User-Email: email -> (sub가 이메일 형식이면 sub)
 * 3) X-User-Role : role
 */
@Slf4j
@Component
public class JwtAuthenticationFilter implements GlobalFilter, Ordered {

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        return ReactiveSecurityContextHolder.getContext()
                .flatMap(context -> {
                    if (context.getAuthentication() instanceof JwtAuthenticationToken jwtAuth) {
                        Jwt jwt = jwtAuth.getToken();

                        String subject = jwt.getSubject();
                        String userId = extractUserId(jwt, subject);
                        String email = extractEmail(jwt, subject);
                        String role = extractRole(jwt);
                        String departmentId = jwt.getClaimAsString("department_id");

                        String keywords = jwt.getClaimAsString("keywords");

                        log.debug(
                                "JWT Filter - subject: {}, userId: {}, email: {}, role: {}, departmentId: {}, keywords: {}",
                                subject, userId, email, role, departmentId, keywords
                        );

                        ServerHttpRequest mutatedRequest = exchange.getRequest().mutate()
                                .header("X-User-Id",       safe(userId))
                                .header("X-User-Email",    safe(email))
                                .header("X-User-Role",     safe(role))
                                .header("X-Department-Id", safe(departmentId))
                                .header("X-User-Keywords", safe(keywords))
                                .build();

                        return chain.filter(exchange.mutate().request(mutatedRequest).build());
                    }
                    return chain.filter(exchange);
                })
                .switchIfEmpty(chain.filter(exchange));
    }

    /**
     * X-User-Id 추출 우선순위
     * - user_id 클레임
     * - id 클레임
     * - sub
     */
    private String extractUserId(Jwt jwt, String subject) {
        String userId = jwt.getClaimAsString("user_id");
        if (hasText(userId)) {
            return userId;
        }

        userId = jwt.getClaimAsString("id");
        if (hasText(userId)) {
            return userId;
        }

        return subject;
    }

    /**
     * X-User-Email 추출 우선순위
     * - email 클레임
     * - sub가 이메일 형식이면 sub
     */
    private String extractEmail(Jwt jwt, String subject) {
        String email = jwt.getClaimAsString("email");
        if (hasText(email)) {
            return email;
        }

        if (looksLikeEmail(subject)) {
            return subject;
        }

        return "";
    }

    /**
     * X-User-Role 추출
     */
    private String extractRole(Jwt jwt) {
        String role = jwt.getClaimAsString("role");
        return hasText(role) ? role : "";
    }

    private boolean hasText(String value) {
        return value != null && !value.trim().isEmpty();
    }

    private boolean looksLikeEmail(String value) {
        return hasText(value) && value.contains("@");
    }

    private String safe(String value) {
        return value != null ? value : "";
    }

    @Override
    public int getOrder() {
        return -1;
    }
}