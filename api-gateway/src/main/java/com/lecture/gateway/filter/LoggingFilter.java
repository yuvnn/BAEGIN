package com.lecture.gateway.filter;

import lombok.extern.slf4j.Slf4j;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.time.Instant;

/**
 * 모든 요청/응답에 대한 로깅 필터
 * - 요청 경로, 메서드, 처리 시간 기록
 */
@Slf4j
@Component
public class LoggingFilter implements GlobalFilter, Ordered {

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        long startTime = Instant.now().toEpochMilli();

        log.info("[Gateway] → {} {}", request.getMethod(), request.getPath());

        return chain.filter(exchange).then(Mono.fromRunnable(() -> {
            long duration = Instant.now().toEpochMilli() - startTime;
            log.info("[Gateway] ← {} {} | status: {} | {}ms",
                request.getMethod(),
                request.getPath(),
                exchange.getResponse().getStatusCode(),
                duration);
        }));
    }

    @Override
    public int getOrder() {
        return -2; // JwtAuthenticationFilter보다 먼저 실행
    }
}
