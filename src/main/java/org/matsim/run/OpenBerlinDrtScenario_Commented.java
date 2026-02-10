/* *********************************************************************** *
 * project: org.matsim.*
 * OpenBerlinDrtScenario_Commented.java
 *                                                                         *
 * *********************************************************************** *
 * 이 파일은 OpenBerlinDrtScenario.java의 한글 주석 버전입니다.
 * 원본 코드를 수정하지 않고, 각 부분에 대한 상세한 설명을 추가했습니다.
 * *********************************************************************** */

package org.matsim.run;

// ============================================================================
// 1. IMPORT 섹션 - 필요한 라이브러리들
// ============================================================================

// SwissRailRaptor: 고급 대중교통 라우터 (SBB에서 개발)
import ch.sbb.matsim.config.SwissRailRaptorConfigGroup;
import ch.sbb.matsim.routing.pt.raptor.RaptorIntermodalAccessEgress;

import com.beust.jcommander.internal.Lists;
import com.google.common.collect.ImmutableSet;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

// GeoTools: 지리 정보 처리 (Shapefile 읽기 등)
import org.geotools.api.feature.simple.SimpleFeature;
import org.locationtech.jts.geom.Geometry;

// MATSim 핵심 라이브러리
import org.matsim.api.core.v01.Scenario;
import org.matsim.api.core.v01.TransportMode;
import org.matsim.api.core.v01.network.Link;
import org.matsim.application.MATSimApplication;
import org.matsim.application.options.ShpOptions;

// DRT 관련 라이브러리 (contrib/drt에서 가져옴)
import org.matsim.contrib.drt.routing.DrtRoute;
import org.matsim.contrib.drt.routing.DrtRouteFactory;
import org.matsim.contrib.drt.run.DrtConfigGroup;
import org.matsim.contrib.drt.run.DrtConfigs;
import org.matsim.contrib.drt.run.MultiModeDrtConfigGroup;
import org.matsim.contrib.drt.run.MultiModeDrtModule;

// DVRP 관련 라이브러리 (동적 차량 경로 문제 - DRT의 기반 엔진)
import org.matsim.contrib.dvrp.run.DvrpConfigGroup;
import org.matsim.contrib.dvrp.run.DvrpModule;
import org.matsim.contrib.dvrp.run.DvrpQSimComponents;

// 설정(Config) 관련
import org.matsim.core.config.Config;
import org.matsim.core.config.ConfigGroup;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.config.groups.QSimConfigGroup;
import org.matsim.core.config.groups.ScoringConfigGroup;

// Controller: 시뮬레이션 엔진
import org.matsim.core.controler.AbstractModule;
import org.matsim.core.controler.Controler;

// 네트워크 및 라우팅
import org.matsim.core.network.algorithms.MultimodalNetworkCleaner;
import org.matsim.core.population.routes.RouteFactories;
import org.matsim.core.router.AnalysisMainModeIdentifier;
import org.matsim.core.router.MainModeIdentifier;
import org.matsim.core.scenario.ScenarioUtils;
import org.matsim.core.utils.geometry.geotools.MGC;

// 요금 통합 (Intermodal Fare)
import org.matsim.extensions.pt.fare.intermodalTripFareCompensator.IntermodalTripFareCompensatorConfigGroup;
import org.matsim.extensions.pt.fare.intermodalTripFareCompensator.IntermodalTripFareCompensatorsConfigGroup;
import org.matsim.extensions.pt.fare.intermodalTripFareCompensator.IntermodalTripFareCompensatorsModule;
import org.matsim.extensions.pt.routing.EnhancedRaptorIntermodalAccessEgress;
import org.matsim.extensions.pt.routing.ptRoutingModes.PtIntermodalRoutingModesConfigGroup;
import org.matsim.extensions.pt.routing.ptRoutingModes.PtIntermodalRoutingModesModule;

// 베를린 전용 설정
import org.matsim.legacy.run.BerlinExperimentalConfigGroup;
import org.matsim.legacy.run.drt.OpenBerlinIntermodalPtDrtRouterAnalysisModeIdentifier;
import org.matsim.legacy.run.drt.OpenBerlinIntermodalPtDrtRouterModeIdentifier;

// 대중교통 스케줄
import org.matsim.pt.transitSchedule.api.TransitSchedule;
import org.matsim.pt.transitSchedule.api.TransitStopFacility;

// 명령줄 인자 파싱
import picocli.CommandLine;

import java.util.*;

// ============================================================================
// 2. 클래스 정의
// ============================================================================

/**
 * OpenBerlinScenario를 상속받아 DRT 기능을 추가한 클래스입니다.
 * 
 * [핵심 역할]
 * 1. DRT 설정 파일(drt-config.xml)을 로드하여 기본 설정에 병합
 * 2. DRT가 운행할 수 있도록 네트워크(도로망)를 수정
 * 3. 대중교통 정류장 중 DRT와 연계 가능한 정류장에 태그 추가
 * 4. DRT 모듈을 시뮬레이션 엔진에 등록
 * 
 * [상속 구조]
 * MATSimApplication ← OpenBerlinScenario ← OpenBerlinDrtScenario (현재 클래스)
 */
public class OpenBerlinDrtScenario_Commented extends OpenBerlinScenario {

    // 로깅을 위한 Logger 인스턴스
    private static final Logger log = LogManager.getLogger(OpenBerlinDrtScenario.class);

    // ========================================================================
    // 명령줄 옵션 정의
    // ========================================================================
    
    /**
     * --drt-config 옵션: DRT 전용 설정 파일 경로를 지정합니다.
     * 
     * [사용 예시]
     * java -jar matsim.jar run --drt-config my-drt-config.xml
     * 
     * [기본값]
     * input/v6.4/berlin-v6.4.drt-config.xml
     */
    @CommandLine.Option(names = "--drt-config",
        defaultValue = "input/v" + OpenBerlinScenario.VERSION + "/berlin-v" + OpenBerlinScenario.VERSION + ".drt-config.xml",
        description = "Path to drt (only) config. Should contain only additional stuff to base config. Otherwise overrides.")
    private String drtConfig;

    // ========================================================================
    // 메인 진입점
    // ========================================================================
    
    /**
     * 프로그램 시작점.
     * MATSimApplication.run()이 모든 설정 로딩, 시뮬레이션 실행을 처리합니다.
     */
    public static void main(String[] args) {
        MATSimApplication.run(OpenBerlinDrtScenario.class, args);
    }

    // ========================================================================
    // 3. 네트워크 및 대중교통 스케줄 준비 (핵심 로직!)
    // ========================================================================
    
    /**
     * [핵심 메서드 1] 네트워크와 대중교통 스케줄을 DRT용으로 준비합니다.
     * 
     * [하는 일]
     * 1. DRT 서비스 구역(Shapefile) 읽기
     * 2. 서비스 구역 내의 도로(Link)에 'drt' 모드 추가 → addDRTMode()
     * 3. 서비스 구역 내의 주요 역에 'drtStopFilter' 태그 추가 → tagTransitStopsInServiceArea()
     * 
     * @param scenario MATSim 시나리오 (네트워크, 대중교통 스케줄 포함)
     */
    private static void prepareNetworkAndTransitScheduleForDrt(Scenario scenario) {
        // 베를린 실험용 설정 그룹 가져오기 (버퍼 거리 등)
        BerlinExperimentalConfigGroup berlinCfg = ConfigUtils.addOrGetModule(scenario.getConfig(), BerlinExperimentalConfigGroup.class);
        // DVRP 설정 그룹 가져오기 (네트워크 모드 등)
        DvrpConfigGroup dvrpConfigGroup = DvrpConfigGroup.get(scenario.getConfig());

        // 모든 DRT 모드에 대해 반복 (멀티 DRT 지원)
        for (DrtConfigGroup drtCfg : MultiModeDrtConfigGroup.get(scenario.getConfig()).getModalElements()) {
            // 서비스 구역 Shapefile 경로 가져오기
            String drtServiceAreaShapeFile = drtCfg.drtServiceAreaShapeFile;
            
            // 서비스 구역이 정의된 경우에만 처리
            if (drtServiceAreaShapeFile != null && !drtServiceAreaShapeFile.equals("") && !drtServiceAreaShapeFile.equals("null")) {

                // DVRP 네트워크 모드에 이 DRT 모드가 포함되어 있다면
                if (dvrpConfigGroup.networkModes.contains(drtCfg.getMode())) {
                    // [성능 최적화] DRT 네트워크를 서비스 구역 크기에 맞게 제한하면 속도가 빨라집니다.
                    // 버퍼(5000m 기본값)를 두어 구역 경계 근처의 도로도 포함합니다.
                    if (berlinCfg.getTagDrtLinksBufferAroundServiceAreaShp() >= 0.0) {
                        // ★★★ 네트워크에 DRT 모드 추가 ★★★
                        addDRTMode(scenario, drtCfg.getMode(), drtServiceAreaShapeFile, berlinCfg.getTagDrtLinksBufferAroundServiceAreaShp());
                    }
                }

                // ★★★ 대중교통 정류장에 DRT 연계 태그 추가 ★★★
                tagTransitStopsInServiceArea(scenario.getTransitSchedule(),
                    "drtStopFilter",                         // 새로 추가할 속성 이름
                    "station_S/U/RE/RB_drtServiceArea",      // 새로 추가할 속성 값
                    drtServiceAreaShapeFile,                  // 서비스 구역 Shapefile
                    "stopFilter",                             // 기존 필터 속성 이름
                    "station_S/U/RE/RB",                      // 기존 필터 속성 값 (주요 역만)
                    200.0);                                   // 버퍼 거리 (미터) - 구역 경계 근처 역 포함
            }
        }
    }

    // ========================================================================
    // 4. 대중교통 정류장 태깅
    // ========================================================================
    
    /**
     * [핵심 메서드 2] 서비스 구역 내의 주요 대중교통 역에 DRT 연계 태그를 추가합니다.
     * 
     * [목적]
     * SwissRailRaptor가 경로를 탐색할 때, 이 태그가 있는 역만
     * "DRT를 타고 갈 수 있는 환승 거점"으로 인식하게 합니다.
     * 
     * [조건]
     * 1. 기존에 "station_S/U/RE/RB" 태그가 있는 역 (주요 역)
     * 2. 서비스 구역(+200m 버퍼) 내에 위치
     * 
     * @param transitSchedule 대중교통 스케줄
     * @param newAttributeName 새로 추가할 속성 이름 ("drtStopFilter")
     * @param newAttributeValue 새로 추가할 속성 값
     * @param drtServiceAreaShapeFile 서비스 구역 Shapefile 경로
     * @param oldFilterAttribute 기존 필터 속성 이름
     * @param oldFilterValue 기존 필터 속성 값
     * @param bufferAroundServiceArea 버퍼 거리 (미터)
     */
    private static void tagTransitStopsInServiceArea(TransitSchedule transitSchedule,
                                                     String newAttributeName, String newAttributeValue,
                                                     String drtServiceAreaShapeFile,
                                                     String oldFilterAttribute, String oldFilterValue,
                                                     double bufferAroundServiceArea) {
        log.info("Tagging pt stops marked for intermodal access/egress in the service area.");
        
        // Shapefile 읽기
        ShpOptions shp = new ShpOptions(drtServiceAreaShapeFile, null, null);
        List<Geometry> serviceAreas = new ArrayList<>();
        
        // 모든 Feature(폴리곤)에 대해 버퍼 적용
        for (SimpleFeature ft : shp.readFeatures()) {
            Geometry geom = (Geometry) ft.getDefaultGeometry();
            // 200m 버퍼 추가 - 구역 경계에 가까운 역도 포함
            serviceAreas.add(geom.buffer(bufferAroundServiceArea));
        }

        // 모든 대중교통 정류장 순회
        for (TransitStopFacility stop : transitSchedule.getFacilities().values()) {
            // 기존 필터 속성이 있는지 확인
            if (stop.getAttributes().getAttribute(oldFilterAttribute) != null) {
                // 주요 역인지 확인 (S-Bahn, U-Bahn, RE, RB)
                // AND 서비스 구역 내에 있는지 확인
                if (stop.getAttributes().getAttribute(oldFilterAttribute).equals(oldFilterValue) &&
                    serviceAreas.stream().anyMatch(geom -> geom.contains(MGC.coord2Point(stop.getCoord())))) {
                    // ★ 두 조건을 모두 만족하면 새 태그 추가 ★
                    stop.getAttributes().putAttribute(newAttributeName, newAttributeValue);
                }
            }
        }
    }

    // ========================================================================
    // 5. 네트워크에 DRT 모드 추가
    // ========================================================================
    
    /**
     * [핵심 메서드 3] 서비스 구역 내의 도로(Link)에 DRT 모드를 추가합니다.
     * 
     * [목적]
     * DRT 차량이 경로를 계산할 때, 이 모드가 허용된 링크만 사용합니다.
     * 즉, 서비스 구역 밖의 도로는 "없는 길"로 취급됩니다.
     * 
     * [로직]
     * 1. 모든 링크를 순회
     * 2. 링크가 'car' 모드를 허용하는지 확인
     * 3. 링크의 시작점 또는 끝점이 서비스 구역 내에 있는지 확인
     * 4. 조건을 만족하면 'drt' 모드를 허용 모드에 추가
     * 
     * @param scenario MATSim 시나리오
     * @param drtNetworkMode DRT 네트워크 모드 이름 ("drt")
     * @param drtServiceAreaShapeFile 서비스 구역 Shapefile 경로
     * @param buffer 버퍼 거리 (미터)
     */
    private static void addDRTMode(Scenario scenario, String drtNetworkMode, String drtServiceAreaShapeFile, double buffer) {

        log.info("Adjusting network...");

        // Shapefile 읽기
        ShpOptions shp = new ShpOptions(drtServiceAreaShapeFile, null, null);
        List<Geometry> serviceAreas = new ArrayList<>();
        for (SimpleFeature ft : shp.readFeatures()) {
            Geometry geom = (Geometry) ft.getDefaultGeometry();
            // 버퍼 적용 (5000m 기본값)
            serviceAreas.add(geom.buffer(buffer));
        }

        // 카운터 초기화
        int counter = 0;
        int counterInside = 0;
        int counterOutside = 0;
        
        // ★ 모든 링크 순회 ★
        for (Link link : scenario.getNetwork().getLinks().values()) {
            // 진행 상황 로깅 (10,000개마다)
            if (counter % 10000 == 0)
                log.info("link #{}", counter);
            counter++;
            
            // [조건 1] 이 링크가 'car' 모드를 허용하는가?
            // (DRT는 자동차 도로를 기반으로 운행)
            if (link.getAllowedModes().contains(TransportMode.car)) {
                
                // [조건 2] 링크의 시작점 또는 끝점이 서비스 구역 내에 있는가?
                if (serviceAreas.stream().anyMatch(geom -> 
                    geom.contains(MGC.coord2Point(link.getFromNode().getCoord())) ||
                    geom.contains(MGC.coord2Point(link.getToNode().getCoord())))) {

                    // ★ 'drt' 모드를 허용 모드에 추가 ★
                    Set<String> allowedModes = new HashSet<>(link.getAllowedModes());
                    allowedModes.add(drtNetworkMode);
                    link.setAllowedModes(allowedModes);
                    
                    counterInside++;
                } else {
                    counterOutside++;
                }
            }
        }

        // 결과 로깅
        log.info("Total links: {}", counter);
        log.info("Total links inside service area: {}", counterInside);
        log.info("Total links outside service area: {}", counterOutside);

        // ★ 네트워크 정리 ★
        // 고립된 링크(다른 drt 링크와 연결되지 않은 링크) 제거
        Set<String> modes = new HashSet<>();
        modes.add(drtNetworkMode);
        new MultimodalNetworkCleaner(scenario.getNetwork()).run(modes);
    }

    // ========================================================================
    // 6. 커스텀 설정 모듈 등록
    // ========================================================================
    
    /**
     * DRT 시뮬레이션에 필요한 추가 설정 그룹들을 반환합니다.
     * 
     * [추가되는 모듈]
     * - BerlinExperimentalConfigGroup: 베를린 실험용 설정
     * - DvrpConfigGroup: 동적 차량 경로 문제(DVRP) 설정
     * - MultiModeDrtConfigGroup: 다중 DRT 모드 설정
     * - SwissRailRaptorConfigGroup: 고급 대중교통 라우터 설정
     * - IntermodalTripFareCompensatorsConfigGroup: 복합 교통 요금 통합 설정
     * - PtIntermodalRoutingModesConfigGroup: 복합 교통 라우팅 모드 설정
     */
    @Override
    protected List<ConfigGroup> getCustomModules() {
        List<ConfigGroup> customModules = super.getCustomModules();
        customModules.addAll(Lists.newArrayList(
            new BerlinExperimentalConfigGroup(),
            new DvrpConfigGroup(),
            new MultiModeDrtConfigGroup(),
            new SwissRailRaptorConfigGroup(),
            new IntermodalTripFareCompensatorsConfigGroup(),
            new PtIntermodalRoutingModesConfigGroup()));
        return customModules;
    }

    // ========================================================================
    // 7. 설정(Config) 준비 (파라미터 설정)
    // ========================================================================
    
    /**
     * [핵심 메서드 4] 설정 파일을 로드하고 DRT 관련 설정을 추가합니다.
     * 
     * [순서]
     * 1. 부모 클래스(OpenBerlinScenario)의 prepareConfig() 호출
     * 2. DRT 전용 설정 파일(drt-config.xml) 병합
     * 3. 출력 디렉토리 및 Run ID에 "-drt" 접미사 추가
     * 4. QSim 시작 시간 설정
     * 5. DRT 모드의 Scoring 파라미터를 PT에서 복사
     * 6. 요금 통합 설정 (DRT + PT 통합 요금)
     * 7. Mode Choice에 DRT 추가
     */
    @Override
    protected Config prepareConfig(Config config) {
        // 부모 클래스의 설정 준비 먼저 실행
        super.prepareConfig(config);

        // DRT 전용 설정 파일 병합
        ConfigUtils.loadConfig(config, drtConfig);

        // 출력 디렉토리와 Run ID에 "-drt" 접미사 추가
        config.controller().setOutputDirectory(config.controller().getOutputDirectory() + "-drt");
        config.controller().setRunId(config.controller().getRunId() + "-drt");

        // DRT는 이 시작 시간 해석 방식에서만 작동합니다
        config.qsim().setSimStarttimeInterpretation(QSimConfigGroup.StarttimeInterpretation.onlyUseStarttime);

        // DRT 설정 조정 (내부적으로 필요한 파라미터 자동 설정)
        MultiModeDrtConfigGroup multiModeDrtCfg = MultiModeDrtConfigGroup.get(config);
        DrtConfigs.adjustMultiModeDrtConfig(multiModeDrtCfg, config.scoring(), config.routing());

        // DRT 모드 이름들을 저장할 Set
        Set<String> drtModes = new HashSet<>();

        // ★ PT(대중교통)의 Scoring 파라미터 가져오기 ★
        ScoringConfigGroup.ModeParams ptParams = config.scoring().getModes().get(TransportMode.pt);
        IntermodalTripFareCompensatorsConfigGroup compensatorsConfig = ConfigUtils.addOrGetModule(config, IntermodalTripFareCompensatorsConfigGroup.class);

        // 각 DRT 모드에 대해 설정 추가
        for (DrtConfigGroup drtCfg : multiModeDrtCfg.getModalElements()) {
            drtModes.add(drtCfg.getMode());

            // ★★★ DRT의 Scoring 파라미터를 PT에서 복사 ★★★
            // 이렇게 하면 DRT가 PT와 동일한 선호도/비용으로 인식됩니다
            ScoringConfigGroup.ModeParams modeParams = new ScoringConfigGroup.ModeParams(drtCfg.getMode());
            modeParams.setConstant(ptParams.getConstant());                           // 기본 선호도
            modeParams.setMarginalUtilityOfDistance(ptParams.getMarginalUtilityOfDistance());  // 거리당 효용
            modeParams.setMarginalUtilityOfTraveling(ptParams.getMarginalUtilityOfTraveling()); // 시간당 효용
            modeParams.setDailyUtilityConstant(ptParams.getDailyUtilityConstant());   // 일일 고정 효용

            // 요금 통합: DRT를 PT 요금 체계에 완전히 통합
            modeParams.setMonetaryDistanceRate(ptParams.getMonetaryDistanceRate());   // 거리당 요금
            modeParams.setDailyMonetaryConstant(ptParams.getDailyMonetaryConstant()); // 일일 고정 요금
            config.scoring().addModeParams(modeParams);
        }

        // ★★★ 요금 보상 설정 ★★★
        // "같은 날 PT를 탔다면, DRT 요금을 보상(환불)해준다"
        // → 결과적으로 DRT+PT 환승 시 이중 요금 방지
        IntermodalTripFareCompensatorConfigGroup drtCompensationCfg = new IntermodalTripFareCompensatorConfigGroup();
        drtCompensationCfg.setCompensationCondition(IntermodalTripFareCompensatorConfigGroup.CompensationCondition.PtModeUsedAnywhereInTheDay);
        drtCompensationCfg.setCompensationMoneyPerDay(ptParams.getDailyMonetaryConstant());
        drtCompensationCfg.setNonPtModes(ImmutableSet
            .<String>builder()
            .addAll(drtModes)
            .build());
        compensatorsConfig.addParameterSet(drtCompensationCfg);

        // ★★★ Mode Choice에 DRT 추가 ★★★
        // 에이전트가 교통수단을 선택할 때 DRT도 고려하게 합니다
        drtModes.addAll(Arrays.asList(config.subtourModeChoice().getModes()));
        config.subtourModeChoice().setModes(drtModes.toArray(String[]::new));

        return config;
    }

    // ========================================================================
    // 8. 시나리오 생성
    // ========================================================================
    
    /**
     * 시나리오를 생성하고 DRT Route Factory를 등록합니다.
     * 
     * [주의]
     * DrtRouteFactory를 먼저 등록해야 plans.xml에 DRT 경로가 있어도 문제없이 로드됩니다.
     */
    @Override
    protected Scenario createScenario(Config config) {
        Scenario scenario = ScenarioUtils.createScenario(config);

        // DRT 경로 팩토리 등록 (plans.xml에 DRT 경로가 있을 경우 대비)
        RouteFactories routeFactories = scenario.getPopulation().getFactory().getRouteFactories();
        routeFactories.setRouteFactory(DrtRoute.class, new DrtRouteFactory());

        // 시나리오 로드 (네트워크, 인구, 대중교통 스케줄 등)
        ScenarioUtils.loadScenario(scenario);
        return scenario;
    }

    // ========================================================================
    // 9. 시나리오 준비 (데이터 수정)
    // ========================================================================
    
    /**
     * 시나리오 데이터(네트워크, 대중교통 스케줄)를 DRT용으로 수정합니다.
     */
    @Override
    protected void prepareScenario(Scenario scenario) {
        // 부모 클래스의 준비 작업 먼저 실행
        super.prepareScenario(scenario);

        // ★★★ 네트워크 및 대중교통 정류장 수정 ★★★
        // - 서비스 구역 내의 링크에 'drt' 모드 추가
        // - 서비스 구역 내의 주요 역에 'drtStopFilter' 태그 추가
        prepareNetworkAndTransitScheduleForDrt(scenario);
    }

    // ========================================================================
    // 10. Controller 준비 (시뮬레이션 엔진 설정)
    // ========================================================================
    
    /**
     * [핵심 메서드 5] 시뮬레이션 엔진(Controller)에 DRT 모듈을 등록합니다.
     * 
     * [등록되는 모듈]
     * 1. MultiModeDrtModule: DRT 핵심 엔진 (배차, 라우팅, 최적화)
     * 2. DvrpModule: 동적 차량 경로 문제 엔진
     * 3. IntermodalTripFareCompensatorsModule: 복합 교통 요금 보상
     * 4. PtIntermodalRoutingModesModule: 복합 교통 라우팅
     * 
     * [바인딩]
     * - AnalysisMainModeIdentifier: pt_w_drt_used 등의 분석용 모드 식별
     * - MainModeIdentifier: 주요 교통수단 식별
     * - RaptorIntermodalAccessEgress: DRT를 PT 접근 수단으로 사용
     */
    @Override
    protected void prepareControler(Controler controler) {
        // 부모 클래스의 Controller 준비 먼저 실행
        super.prepareControler(controler);

        // ★★★ DRT + DVRP 핵심 모듈 등록 ★★★
        controler.addOverridingModule(new MultiModeDrtModule());  // DRT 핵심 엔진
        controler.addOverridingModule(new DvrpModule());          // 동적 차량 경로 엔진
        
        // QSim에 DRT 모드 활성화
        controler.configureQSimComponents(DvrpQSimComponents.activateAllModes(MultiModeDrtConfigGroup.get(controler.getConfig())));

        // ★★★ 커스텀 바인딩 모듈 ★★★
        controler.addOverridingModule(new AbstractModule() {
            @Override
            public void install() {
                // 분석용 모드 식별자 바인딩 (pt_w_drt_used 집계를 위해)
                bind(AnalysisMainModeIdentifier.class).to(OpenBerlinIntermodalPtDrtRouterAnalysisModeIdentifier.class);
                // 주요 모드 식별자 바인딩
                bind(MainModeIdentifier.class).to(OpenBerlinIntermodalPtDrtRouterModeIdentifier.class);
                // 대중교통 라우터의 Intermodal 접근/이탈 기능 확장
                bind(RaptorIntermodalAccessEgress.class).to(EnhancedRaptorIntermodalAccessEgress.class);
            }
        });

        // 요금 보상 모듈 등록
        controler.addOverridingModule(new IntermodalTripFareCompensatorsModule());
        // 복합 교통 라우팅 모드 모듈 등록
        controler.addOverridingModule(new PtIntermodalRoutingModesModule());
    }
}
