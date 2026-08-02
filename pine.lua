// This Pine Script® code is subject to the terms of the Mozilla Public License 2.0.
// SPDX-License-Identifier: MPL-2.0
// Independent multi-timeframe swing, VWAP, and liquidity strategy.
// No third-party brand names, logos, marketing text, or external libraries are included.
//
// Designed for separate backtests on 1-minute, 15-minute, and 1-hour charts.
// The strategy automatically selects a profile for the active chart timeframe.
// Orders and Strategy Tester results always belong to the active chart timeframe only.
//
//@version=6
//@strategy_alert_message {{strategy.order.alert_message}}
strategy(
     "IMSTE Multi-Timeframe Swing VWAP & Liquidity Strategy",
     shorttitle = "IMSTE",
     overlay = true,
     pyramiding = 0,
     initial_capital = 100000,
     default_qty_type = strategy.percent_of_equity,
     default_qty_value = 10,
     commission_type = strategy.commission.percent,
     commission_value = 0.05,
     slippage = 1,
     process_orders_on_close = true,
     calc_on_order_fills = false,
     calc_on_every_tick = false,
     max_bars_back = 5000,
     max_lines_count = 200,
     max_labels_count = 400)

// ============================================================================
// INPUT GROUPS
// ============================================================================
string GRP_PROFILE = "1. Timeframe Profiles"
string GRP_SWING   = "2. Swing and Liquidity"
string GRP_FILTER  = "3. Signal Filters"
string GRP_RISK    = "4. Backtest Risk and Exits"
string GRP_VISUAL  = "5. Chart Display"

// Profile selection
string profileMode = input.string("Auto", "Signal Profile", options = ["Auto", "1 Minute", "15 Minute", "1 Hour", "Custom"], group = GRP_PROFILE, display = display.none)
string selectivity = input.string("Balanced", "Signal Selectivity", options = ["Conservative", "Balanced", "Aggressive"], group = GRP_PROFILE, display = display.none)
bool useConfirmedHtf = input.bool(true, "Use Confirmed Higher-Timeframe Trend", group = GRP_PROFILE, display = display.none)
bool showMtfPanel = input.bool(true, "Show 1m / 15m / 1h Context Panel", group = GRP_PROFILE, display = display.none)

// Custom profile values
int customSwingLen = input.int(5, "Custom Swing Length", minval = 2, maxval = 30, group = GRP_PROFILE, display = display.none)
int customFastLen = input.int(20, "Custom Fast EMA", minval = 2, maxval = 300, group = GRP_PROFILE, display = display.none)
int customSlowLen = input.int(50, "Custom Slow EMA", minval = 3, maxval = 500, group = GRP_PROFILE, display = display.none)
int customAnchorLen = input.int(200, "Custom Anchor EMA", minval = 20, maxval = 1000, group = GRP_PROFILE, display = display.none)
string customHtf = input.timeframe("240", "Custom Confirmation Timeframe", group = GRP_PROFILE, display = display.none)
float customMinimumScore = input.float(72.0, "Custom Minimum Signal Score", minval = 50, maxval = 95, step = 1, group = GRP_PROFILE, display = display.none)

// Swing and liquidity
bool showSwingLevels = input.bool(true, "Show Latest Swing Liquidity", group = GRP_SWING, display = display.none)
bool showEqualLiquidity = input.bool(true, "Show Equal-High/Low Liquidity Pools", group = GRP_SWING, display = display.none)
float equalToleranceAtr = input.float(0.12, "Equal-Level Tolerance (ATR)", minval = 0.01, maxval = 1.0, step = 0.01, group = GRP_SWING, display = display.none)
int liquidityMaxAge = input.int(150, "Liquidity Pool Maximum Age", minval = 10, maxval = 2000, group = GRP_SWING, display = display.none)
int maxLiquidityPools = input.int(20, "Maximum Equal-Level Pools", minval = 2, maxval = 80, group = GRP_SWING, display = display.none)
float sweepWickAtr = input.float(0.10, "Minimum Liquidity-Sweep Wick (ATR)", minval = 0.0, maxval = 3.0, step = 0.05, group = GRP_SWING, display = display.none)
int sweepConfirmationBars = input.int(3, "Bars Allowed for VWAP Confirmation after Sweep", minval = 0, maxval = 20, group = GRP_SWING, display = display.none)

// Filters
bool requireConfirmedClose = input.bool(true, "Require Confirmed Bar Close", group = GRP_FILTER, display = display.none)
bool useRegularSession = input.bool(true, "Restrict Intraday Signals to Regular Session", group = GRP_FILTER, display = display.none)
string regularSession = input.session("0930-1600", "Regular Session", group = GRP_FILTER, display = display.none)
string sessionTimezone = input.string("America/New_York", "Session Time Zone", options = ["America/New_York", "Europe/London", "Asia/Tokyo", "UTC"], group = GRP_FILTER, display = display.none)
bool useRelativeVolume = input.bool(true, "Use Relative-Volume Filter", group = GRP_FILTER, display = display.none)
bool avoidLowVolatility = input.bool(true, "Suppress Low-Volatility Signals", group = GRP_FILTER, display = display.none)
bool requireFlowAlignment = input.bool(true, "Require Candle-Volume Flow Alignment", group = GRP_FILTER, display = display.none)
bool allowSweepEntries = input.bool(true, "Allow Liquidity-Sweep Entries", group = GRP_FILTER, display = display.none)
bool allowBreakoutEntries = input.bool(true, "Allow Swing-Breakout Entries", group = GRP_FILTER, display = display.none)
bool allowPullbackEntries = input.bool(true, "Allow Higher-Low / Lower-High Pullback Entries", group = GRP_FILTER, display = display.none)
string allowedDirection = input.string("Both", "Allowed Direction", options = ["Both", "Long Only", "Short Only"], group = GRP_FILTER, display = display.none)
bool closeOnOppositeSignal = input.bool(true, "Reverse on Opposite Signal", group = GRP_FILTER, display = display.none)

// Risk and backtest
bool enableOrders = input.bool(true, "Enable Strategy Orders", group = GRP_RISK, display = display.none)
int backtestStart = input.time(timestamp("01 Jan 2020 00:00 +0000"), "Backtest Start", group = GRP_RISK, display = display.none)
int backtestEnd = input.time(timestamp("31 Dec 2099 23:59 +0000"), "Backtest End", group = GRP_RISK, display = display.none)
string stopMethod = input.string("Swing with ATR Limits", "Stop Method", options = ["Swing with ATR Limits", "ATR Only"], group = GRP_RISK, display = display.none)
float targetOneQuantity = input.float(50.0, "Target 1 Position %", minval = 1.0, maxval = 99.0, step = 1.0, group = GRP_RISK, display = display.none)
bool moveStopToBreakeven = input.bool(true, "Move Remaining Stop after TP1", group = GRP_RISK, display = display.none)
float breakevenBufferR = input.float(0.05, "Breakeven Profit Buffer (R)", minval = 0.0, maxval = 1.0, step = 0.05, group = GRP_RISK, display = display.none)
bool useAtrTrailAfterTp1 = input.bool(true, "Use ATR Trail after TP1", group = GRP_RISK, display = display.none)
bool exitOnTrendFailure = input.bool(true, "Exit on Confirmed VWAP/EMA Trend Failure", group = GRP_RISK, display = display.none)

// Visuals
bool showVWAP = input.bool(true, "Show VWAP", group = GRP_VISUAL, display = display.none)
bool showFastEma = input.bool(false, "Show Fast EMA", group = GRP_VISUAL, display = display.none)
bool showTrendColor = input.bool(true, "Color Candles Bull/Bear", group = GRP_VISUAL, display = display.none)
bool showEntryLabels = input.bool(true, "Show Timeframe Buy/Sell Labels", group = GRP_VISUAL, display = display.none)
bool showRiskLevels = input.bool(false, "Show Entry, Stop, and Targets", group = GRP_VISUAL, display = display.none)
int rightLabelOffset = input.int(4, "Right Label Offset", minval = 1, maxval = 30, group = GRP_VISUAL, display = display.none)

color bullColor = input.color(#00c853, "Bull Color", group = GRP_VISUAL, display = display.none)
color bearColor = input.color(#ff1744, "Bear Color", group = GRP_VISUAL, display = display.none)
color vwapColor = input.color(#ffd600, "VWAP Color", group = GRP_VISUAL, display = display.none)
color buyLiquidityColor = input.color(#ef5350, "Buy-Side Liquidity Color", group = GRP_VISUAL, display = display.none)
color sellLiquidityColor = input.color(#26a69a, "Sell-Side Liquidity Color", group = GRP_VISUAL, display = display.none)

// ============================================================================
// HELPERS
// ============================================================================
f_clamp(float value, float lower, float upper) =>
    math.max(lower, math.min(upper, value))

f_levelText(string levelName, float levelPrice) =>
    levelName + "  " + str.tostring(levelPrice, format.mintick)

f_deleteLineLabel(line currentLine, label currentLabel) =>
    if not na(currentLine)
        line.delete(currentLine)
    if not na(currentLabel)
        label.delete(currentLabel)

f_stateText(int state) =>
    state == 1 ? "BUY BIAS" : state == -1 ? "SELL BIAS" : "WAIT"

f_stateColor(int state) =>
    state == 1 ? bullColor : state == -1 ? bearColor : color.silver

// Lightweight confirmed context used only by the multi-timeframe panel.
f_contextState(int fastLength, int slowLength, int anchorLength, float bullRsiLevel, float bearRsiLevel) =>
    float contextFast = ta.ema(close, fastLength)
    float contextSlow = ta.ema(close, slowLength)
    float contextAnchor = ta.ema(close, anchorLength)
    float contextVwap = ta.vwap(hlc3)
    float contextRsi = ta.rsi(close, 14)
    bool contextBull = close > contextVwap and contextFast > contextSlow and close > contextAnchor and contextRsi >= bullRsiLevel
    bool contextBear = close < contextVwap and contextFast < contextSlow and close < contextAnchor and contextRsi <= bearRsiLevel
    contextBull ? 1 : contextBear ? -1 : 0

// ============================================================================
// ACTIVE PROFILE
// ============================================================================
float chartSeconds = timeframe.in_seconds(timeframe.period)
bool isOneMinuteChart = chartSeconds == 60
bool isFifteenMinuteChart = chartSeconds == 900
bool isOneHourChart = chartSeconds == 3600

string activeProfile = profileMode == "Auto" ?
     isOneMinuteChart ? "1 Minute" :
     isFifteenMinuteChart ? "15 Minute" :
     isOneHourChart ? "1 Hour" : "Custom" : profileMode

bool profileOneMinute = activeProfile == "1 Minute"
bool profileFifteenMinute = activeProfile == "15 Minute"
bool profileOneHour = activeProfile == "1 Hour"

int effectiveSwingLen = profileOneMinute ? 3 : profileFifteenMinute ? 4 : profileOneHour ? 5 : customSwingLen
int effectiveFastLen = profileOneMinute ? 9 : profileFifteenMinute ? 20 : profileOneHour ? 20 : customFastLen
int effectiveSlowLen = profileOneMinute ? 21 : profileFifteenMinute ? 50 : profileOneHour ? 50 : customSlowLen
int effectiveAnchorLen = profileOneMinute ? 100 : profileFifteenMinute ? 200 : profileOneHour ? 200 : customAnchorLen
string effectiveHtf = profileOneMinute ? "15" : profileFifteenMinute ? "60" : profileOneHour ? "240" : customHtf

float baseMinimumScore = profileOneMinute ? 78.0 : profileFifteenMinute ? 72.0 : profileOneHour ? 68.0 : customMinimumScore
float selectivityAdjustment = selectivity == "Conservative" ? 5.0 : selectivity == "Aggressive" ? -5.0 : 0.0
float effectiveMinimumScore = f_clamp(baseMinimumScore + selectivityAdjustment, 50.0, 95.0)
float baseScoreGap = profileOneMinute ? 12.0 : profileFifteenMinute ? 8.0 : profileOneHour ? 6.0 : 8.0
float scoreGapAdjustment = selectivity == "Conservative" ? 2.0 : selectivity == "Aggressive" ? -2.0 : 0.0
float effectiveScoreGap = math.max(2.0, baseScoreGap + scoreGapAdjustment)

float effectiveBullRsi = profileOneMinute ? 55.0 : profileFifteenMinute ? 53.0 : profileOneHour ? 52.0 : 53.0
float effectiveBearRsi = profileOneMinute ? 45.0 : profileFifteenMinute ? 47.0 : profileOneHour ? 48.0 : 47.0
float effectiveMinimumAdx = profileOneMinute ? 22.0 : profileFifteenMinute ? 18.0 : profileOneHour ? 16.0 : 18.0
float effectiveMinimumRvol = profileOneMinute ? 1.10 : profileFifteenMinute ? 0.90 : profileOneHour ? 0.75 : 0.90
float effectiveMinimumBodyRatio = profileOneMinute ? 0.50 : profileFifteenMinute ? 0.42 : profileOneHour ? 0.35 : 0.42
float effectiveMinimumAtrRatio = profileOneMinute ? 0.85 : profileFifteenMinute ? 0.75 : profileOneHour ? 0.70 : 0.75
int effectiveCooldownBars = profileOneMinute ? 8 : profileFifteenMinute ? 4 : profileOneHour ? 2 : 4

float effectiveAtrStop = profileOneMinute ? 1.10 : profileFifteenMinute ? 1.50 : profileOneHour ? 2.00 : 1.50
float effectiveMinimumStopAtr = profileOneMinute ? 0.60 : profileFifteenMinute ? 0.80 : profileOneHour ? 1.00 : 0.80
float effectiveMaximumStopAtr = profileOneMinute ? 1.80 : profileFifteenMinute ? 2.50 : profileOneHour ? 3.50 : 2.50
float effectiveSwingBufferAtr = profileOneMinute ? 0.08 : profileFifteenMinute ? 0.12 : profileOneHour ? 0.18 : 0.12
float effectiveTargetOneR = profileOneMinute ? 1.00 : profileFifteenMinute ? 1.25 : profileOneHour ? 1.50 : 1.25
float effectiveTargetTwoR = profileOneMinute ? 1.80 : profileFifteenMinute ? 2.50 : profileOneHour ? 3.00 : 2.50
float effectiveTrailAtr = profileOneMinute ? 1.00 : profileFifteenMinute ? 1.35 : profileOneHour ? 1.75 : 1.35
int effectiveMaximumBars = profileOneMinute ? 90 : profileFifteenMinute ? 40 : profileOneHour ? 30 : 40

string profileTag = profileOneMinute ? "1M" : profileFifteenMinute ? "15M" : profileOneHour ? "1H" : timeframe.period

// ============================================================================
// CORE SERIES
// ============================================================================
float atr = ta.atr(14)
float safeAtr = math.max(atr, syminfo.mintick)
float atrAverage = ta.sma(safeAtr, 50)
float atrRatio = safeAtr / math.max(atrAverage, syminfo.mintick)

float emaFast = ta.ema(close, effectiveFastLen)
float emaSlow = ta.ema(close, effectiveSlowLen)
float emaAnchor = ta.ema(close, effectiveAnchorLen)
float rsi = ta.rsi(close, 14)
[plusDi, minusDi, adx] = ta.dmi(14, 14)

bool changedDay = timeframe.change("D")
bool changedWeek = timeframe.change("W")
bool changedYear = timeframe.change("12M")
bool vwapAnchorReset = timeframe.isintraday ? changedDay : timeframe.isdaily ? changedWeek : changedYear
float anchoredVwap = ta.vwap(hlc3, vwapAnchorReset)
float referenceVwap = na(anchoredVwap) ? hlc3 : anchoredVwap

float volumeAverage = ta.sma(nz(volume, 0.0), 20)
bool validVolumeData = not na(volume) and volumeAverage > 0
float relativeVolume = validVolumeData ? volume / volumeAverage : 1.0

float candleRange = math.max(high - low, syminfo.mintick)
float candleBody = math.abs(close - open)
float candleBodyRatio = candleBody / candleRange
float closeLocation = f_clamp(((close - low) - (high - close)) / candleRange, -1.0, 1.0)
float deltaProxy = nz(volume, 0.0) * closeLocation
float deltaEma = ta.ema(deltaProxy, 8)

bool bullishEntryCandle = close > open and candleBodyRatio >= effectiveMinimumBodyRatio
bool bearishEntryCandle = close < open and candleBodyRatio >= effectiveMinimumBodyRatio
bool flowBull = deltaEma > 0
bool flowBear = deltaEma < 0

bool emaBull = emaFast > emaSlow and close > emaAnchor and emaFast >= emaFast[1]
bool emaBear = emaFast < emaSlow and close < emaAnchor and emaFast <= emaFast[1]
bool vwapBull = close > referenceVwap and referenceVwap >= referenceVwap[1]
bool vwapBear = close < referenceVwap and referenceVwap <= referenceVwap[1]
bool momentumBull = rsi >= effectiveBullRsi
bool momentumBear = rsi <= effectiveBearRsi
bool adxBull = adx >= effectiveMinimumAdx and plusDi > minusDi
bool adxBear = adx >= effectiveMinimumAdx and minusDi > plusDi
bool relativeVolumeBull = not useRelativeVolume or not validVolumeData or relativeVolume >= effectiveMinimumRvol
bool relativeVolumeBear = not useRelativeVolume or not validVolumeData or relativeVolume >= effectiveMinimumRvol
bool volatilityGate = not avoidLowVolatility or atrRatio >= effectiveMinimumAtrRatio
bool flowBullGate = not requireFlowAlignment or flowBull
bool flowBearGate = not requireFlowAlignment or flowBear

// Confirmed higher-timeframe values. The [1] offset requests the prior completed
// higher-timeframe candle while lookahead_on aligns that confirmed value to the chart.
[htfFastRequested, htfSlowRequested, htfAnchorRequested, htfCloseRequested] = request.security(
     syminfo.tickerid,
     effectiveHtf,
     [ta.ema(close, effectiveFastLen)[1], ta.ema(close, effectiveSlowLen)[1], ta.ema(close, effectiveAnchorLen)[1], close[1]],
     lookahead = barmerge.lookahead_on)

float htfSeconds = timeframe.in_seconds(effectiveHtf)
bool selectedHtfIsHigher = not na(htfSeconds) and not na(chartSeconds) and htfSeconds > chartSeconds
float htfFast = useConfirmedHtf and selectedHtfIsHigher ? htfFastRequested : emaFast
float htfSlow = useConfirmedHtf and selectedHtfIsHigher ? htfSlowRequested : emaSlow
float htfAnchor = useConfirmedHtf and selectedHtfIsHigher ? htfAnchorRequested : emaAnchor
float htfClose = useConfirmedHtf and selectedHtfIsHigher ? htfCloseRequested : close
bool htfBull = htfFast > htfSlow and htfClose > htfAnchor
bool htfBear = htfFast < htfSlow and htfClose < htfAnchor

bool inRegularSession = not na(time(timeframe.period, regularSession, sessionTimezone))
bool sessionGate = not useRegularSession or not timeframe.isintraday or inRegularSession
bool barGate = not requireConfirmedClose or barstate.isconfirmed

// ============================================================================
// CONFIRMED SWINGS
// ============================================================================
float confirmedPivotHigh = ta.pivothigh(high, effectiveSwingLen, effectiveSwingLen)
float confirmedPivotLow = ta.pivotlow(low, effectiveSwingLen, effectiveSwingLen)

var float lastSwingHigh = na
var float previousSwingHigh = na
var int lastSwingHighBar = na
var float lastSwingLow = na
var float previousSwingLow = na
var int lastSwingLowBar = na

if not na(confirmedPivotHigh)
    previousSwingHigh := lastSwingHigh
    lastSwingHigh := confirmedPivotHigh
    lastSwingHighBar := bar_index - effectiveSwingLen

if not na(confirmedPivotLow)
    previousSwingLow := lastSwingLow
    lastSwingLow := confirmedPivotLow
    lastSwingLowBar := bar_index - effectiveSwingLen

bool higherLowStructure = not na(lastSwingLow) and not na(previousSwingLow) and lastSwingLow > previousSwingLow
bool lowerHighStructure = not na(lastSwingHigh) and not na(previousSwingHigh) and lastSwingHigh < previousSwingHigh

// ============================================================================
// LATEST SWING LIQUIDITY LINES
// ============================================================================
var line latestBuyLiquidityLine = na
var line latestSellLiquidityLine = na
var label latestBuyLiquidityLabel = na
var label latestSellLiquidityLabel = na

if not na(confirmedPivotHigh)
    f_deleteLineLabel(latestBuyLiquidityLine, latestBuyLiquidityLabel)
    latestBuyLiquidityLine := showSwingLevels ? line.new(lastSwingHighBar, lastSwingHigh, bar_index + 20, lastSwingHigh, extend = extend.right, color = color.new(buyLiquidityColor, 20), style = line.style_dashed, width = 1) : na
    latestBuyLiquidityLabel := showSwingLevels ? label.new(bar_index + rightLabelOffset, lastSwingHigh, f_levelText("BUY-SIDE LIQUIDITY", lastSwingHigh), xloc = xloc.bar_index, yloc = yloc.price, style = label.style_label_left, color = color.new(buyLiquidityColor, 15), textcolor = color.white, size = size.tiny) : na

if not na(confirmedPivotLow)
    f_deleteLineLabel(latestSellLiquidityLine, latestSellLiquidityLabel)
    latestSellLiquidityLine := showSwingLevels ? line.new(lastSwingLowBar, lastSwingLow, bar_index + 20, lastSwingLow, extend = extend.right, color = color.new(sellLiquidityColor, 20), style = line.style_dashed, width = 1) : na
    latestSellLiquidityLabel := showSwingLevels ? label.new(bar_index + rightLabelOffset, lastSwingLow, f_levelText("SELL-SIDE LIQUIDITY", lastSwingLow), xloc = xloc.bar_index, yloc = yloc.price, style = label.style_label_left, color = color.new(sellLiquidityColor, 15), textcolor = color.white, size = size.tiny) : na

if barstate.islast
    if showSwingLevels and not na(latestBuyLiquidityLabel) and not na(lastSwingHigh)
        label.set_xy(latestBuyLiquidityLabel, bar_index + rightLabelOffset, lastSwingHigh)
        label.set_text(latestBuyLiquidityLabel, f_levelText("BUY-SIDE LIQUIDITY", lastSwingHigh))
    if showSwingLevels and not na(latestSellLiquidityLabel) and not na(lastSwingLow)
        label.set_xy(latestSellLiquidityLabel, bar_index + rightLabelOffset, lastSwingLow)
        label.set_text(latestSellLiquidityLabel, f_levelText("SELL-SIDE LIQUIDITY", lastSwingLow))

// ============================================================================
// EQUAL-HIGH / EQUAL-LOW LIQUIDITY POOLS
// ============================================================================
var array<line> poolLines = array.new<line>()
var array<label> poolLabels = array.new<label>()
var array<float> poolPrices = array.new<float>()
var array<bool> poolIsHigh = array.new<bool>()
var array<int> poolBirthBars = array.new<int>()

f_removePool(int index) =>
    line poolLine = array.get(poolLines, index)
    label poolLabel = array.get(poolLabels, index)
    if not na(poolLine)
        line.delete(poolLine)
    if not na(poolLabel)
        label.delete(poolLabel)
    array.remove(poolLines, index)
    array.remove(poolLabels, index)
    array.remove(poolPrices, index)
    array.remove(poolIsHigh, index)
    array.remove(poolBirthBars, index)

bool equalHighCreated = showEqualLiquidity and not na(confirmedPivotHigh) and not na(previousSwingHigh) and math.abs(lastSwingHigh - previousSwingHigh) <= equalToleranceAtr * safeAtr
bool equalLowCreated = showEqualLiquidity and not na(confirmedPivotLow) and not na(previousSwingLow) and math.abs(lastSwingLow - previousSwingLow) <= equalToleranceAtr * safeAtr

if equalHighCreated
    line newPoolLine = line.new(lastSwingHighBar, lastSwingHigh, bar_index + 20, lastSwingHigh, extend = extend.right, color = color.new(buyLiquidityColor, 45), style = line.style_dotted)
    label newPoolLabel = label.new(bar_index + rightLabelOffset, lastSwingHigh, "EQ HIGH • BUY LIQ", xloc = xloc.bar_index, yloc = yloc.price, style = label.style_label_left, color = color.new(buyLiquidityColor, 35), textcolor = color.white, size = size.tiny)
    array.push(poolLines, newPoolLine)
    array.push(poolLabels, newPoolLabel)
    array.push(poolPrices, lastSwingHigh)
    array.push(poolIsHigh, true)
    array.push(poolBirthBars, bar_index)

if equalLowCreated
    line newPoolLine = line.new(lastSwingLowBar, lastSwingLow, bar_index + 20, lastSwingLow, extend = extend.right, color = color.new(sellLiquidityColor, 45), style = line.style_dotted)
    label newPoolLabel = label.new(bar_index + rightLabelOffset, lastSwingLow, "EQ LOW • SELL LIQ", xloc = xloc.bar_index, yloc = yloc.price, style = label.style_label_left, color = color.new(sellLiquidityColor, 35), textcolor = color.white, size = size.tiny)
    array.push(poolLines, newPoolLine)
    array.push(poolLabels, newPoolLabel)
    array.push(poolPrices, lastSwingLow)
    array.push(poolIsHigh, false)
    array.push(poolBirthBars, bar_index)

while array.size(poolLines) > maxLiquidityPools
    f_removePool(0)

if array.size(poolLines) > 0
    for i = array.size(poolLines) - 1 to 0
        float poolPrice = array.get(poolPrices, i)
        bool isHighPool = array.get(poolIsHigh, i)
        int poolBirth = array.get(poolBirthBars, i)
        label poolLabel = array.get(poolLabels, i)
        if not na(poolLabel)
            label.set_xy(poolLabel, bar_index + rightLabelOffset, poolPrice)
        bool poolSwept = isHighPool ? high >= poolPrice : low <= poolPrice
        bool poolExpired = bar_index - poolBirth > liquidityMaxAge
        if poolSwept or poolExpired or not showEqualLiquidity
            f_removePool(i)

// ============================================================================
// UNCONDITIONAL STATEFUL EVENT CALCULATIONS
// ============================================================================
bool crossedAboveSwingHigh = ta.crossover(close, lastSwingHigh)
bool crossedBelowSwingLow = ta.crossunder(close, lastSwingLow)
bool crossedAboveVwap = ta.crossover(close, referenceVwap)
bool crossedBelowVwap = ta.crossunder(close, referenceVwap)

bool rawSellSideSweep = not na(lastSwingLow) and low < lastSwingLow and close > lastSwingLow and (lastSwingLow - low) >= sweepWickAtr * safeAtr
bool rawBuySideSweep = not na(lastSwingHigh) and high > lastSwingHigh and close < lastSwingHigh and (high - lastSwingHigh) >= sweepWickAtr * safeAtr
bool sellSideSweep = barGate and rawSellSideSweep and bullishEntryCandle
bool buySideSweep = barGate and rawBuySideSweep and bearishEntryCandle

int barsSinceSellSideSweep = ta.barssince(sellSideSweep)
int barsSinceBuySideSweep = ta.barssince(buySideSweep)
bool recentSellSideSweep = not na(barsSinceSellSideSweep) and barsSinceSellSideSweep <= sweepConfirmationBars
bool recentBuySideSweep = not na(barsSinceBuySideSweep) and barsSinceBuySideSweep <= sweepConfirmationBars

bool bullLiquidityTrigger = allowSweepEntries and ((sellSideSweep and close > referenceVwap) or (recentSellSideSweep and crossedAboveVwap and bullishEntryCandle))
bool bearLiquidityTrigger = allowSweepEntries and ((buySideSweep and close < referenceVwap) or (recentBuySideSweep and crossedBelowVwap and bearishEntryCandle))

bool bullBreakoutTrigger = allowBreakoutEntries and not na(lastSwingHigh) and crossedAboveSwingHigh and bullishEntryCandle
bool bearBreakoutTrigger = allowBreakoutEntries and not na(lastSwingLow) and crossedBelowSwingLow and bearishEntryCandle

bool bullPullbackTrigger = allowPullbackEntries and higherLowStructure and close[1] <= math.max(emaFast[1], referenceVwap[1]) and close > emaFast and close > referenceVwap and bullishEntryCandle
bool bearPullbackTrigger = allowPullbackEntries and lowerHighStructure and close[1] >= math.min(emaFast[1], referenceVwap[1]) and close < emaFast and close < referenceVwap and bearishEntryCandle

bool anyBullTrigger = bullLiquidityTrigger or bullBreakoutTrigger or bullPullbackTrigger
bool anyBearTrigger = bearLiquidityTrigger or bearBreakoutTrigger or bearPullbackTrigger

// ============================================================================
// DIRECTIONAL SCORES AND BUY/SELL SIGNALS
// ============================================================================
float bullScore = 0.0
bullScore += emaBull ? 20.0 : 0.0
bullScore += htfBull ? 20.0 : 0.0
bullScore += vwapBull ? 10.0 : 0.0
bullScore += adxBull ? 15.0 : 0.0
bullScore += momentumBull ? 10.0 : 0.0
bullScore += relativeVolumeBull ? 10.0 : 0.0
bullScore += bullishEntryCandle ? 5.0 : 0.0
bullScore += bullLiquidityTrigger ? 10.0 : bullBreakoutTrigger ? 9.0 : bullPullbackTrigger ? 8.0 : 0.0
bullScore := f_clamp(bullScore, 0.0, 100.0)

float bearScore = 0.0
bearScore += emaBear ? 20.0 : 0.0
bearScore += htfBear ? 20.0 : 0.0
bearScore += vwapBear ? 10.0 : 0.0
bearScore += adxBear ? 15.0 : 0.0
bearScore += momentumBear ? 10.0 : 0.0
bearScore += relativeVolumeBear ? 10.0 : 0.0
bearScore += bearishEntryCandle ? 5.0 : 0.0
bearScore += bearLiquidityTrigger ? 10.0 : bearBreakoutTrigger ? 9.0 : bearPullbackTrigger ? 8.0 : 0.0
bearScore := f_clamp(bearScore, 0.0, 100.0)

var int lastBullSignalBar = na
var int lastBearSignalBar = na
bool bullCooldownOk = na(lastBullSignalBar) or bar_index - lastBullSignalBar >= effectiveCooldownBars
bool bearCooldownOk = na(lastBearSignalBar) or bar_index - lastBearSignalBar >= effectiveCooldownBars

bool bullBaseGate = barGate and sessionGate and volatilityGate and flowBullGate and anyBullTrigger
bool bearBaseGate = barGate and sessionGate and volatilityGate and flowBearGate and anyBearTrigger
bool bullScoreGate = bullScore >= effectiveMinimumScore and bullScore - bearScore >= effectiveScoreGap
bool bearScoreGate = bearScore >= effectiveMinimumScore and bearScore - bullScore >= effectiveScoreGap

bool bullEntrySignal = bullBaseGate and bullScoreGate and bullCooldownOk
bool bearEntrySignal = bearBaseGate and bearScoreGate and bearCooldownOk

if bullEntrySignal
    lastBullSignalBar := bar_index
if bearEntrySignal
    lastBearSignalBar := bar_index

// ============================================================================
// BACKTEST ORDERS — NO DAILY TRADE LIMIT
// ============================================================================
bool inBacktestWindow = time >= backtestStart and time <= backtestEnd
bool allowLong = allowedDirection == "Both" or allowedDirection == "Long Only"
bool allowShort = allowedDirection == "Both" or allowedDirection == "Short Only"
bool canEnterLong = strategy.position_size == 0 or (strategy.position_size < 0 and closeOnOppositeSignal)
bool canEnterShort = strategy.position_size == 0 or (strategy.position_size > 0 and closeOnOppositeSignal)

bool executeBullEntry = enableOrders and inBacktestWindow and allowLong and canEnterLong and bullEntrySignal
bool executeBearEntry = enableOrders and inBacktestWindow and allowShort and canEnterShort and bearEntrySignal

var int activeDirection = 0
var int activeEntryBar = na
var float activeEntry = na
var float activeInitialStop = na
var float activeStop = na
var float activeRisk = na
var float activeTargetOne = na
var float activeTargetTwo = na
var bool targetOneTouched = false
var float highestSinceEntry = na
var float lowestSinceEntry = na

var line entryLine = na
var line stopLine = na
var line targetOneLine = na
var line targetTwoLine = na

if executeBullEntry or executeBearEntry
    bool isLong = executeBullEntry
    float atrStopPrice = isLong ? close - effectiveAtrStop * safeAtr : close + effectiveAtrStop * safeAtr
    float rawSwingStopPrice = isLong ?
         (not na(lastSwingLow) and lastSwingLow < close ? lastSwingLow - effectiveSwingBufferAtr * safeAtr : atrStopPrice) :
         (not na(lastSwingHigh) and lastSwingHigh > close ? lastSwingHigh + effectiveSwingBufferAtr * safeAtr : atrStopPrice)
    float rawStopDistance = math.abs(close - rawSwingStopPrice)
    float clampedStopDistance = f_clamp(rawStopDistance, effectiveMinimumStopAtr * safeAtr, effectiveMaximumStopAtr * safeAtr)
    float swingLimitedStop = isLong ? close - clampedStopDistance : close + clampedStopDistance
    float selectedStop = stopMethod == "ATR Only" ? atrStopPrice : swingLimitedStop
    float riskDistance = math.max(math.abs(close - selectedStop), syminfo.mintick)

    activeDirection := isLong ? 1 : -1
    activeEntryBar := bar_index
    activeEntry := close
    activeInitialStop := selectedStop
    activeStop := selectedStop
    activeRisk := riskDistance
    activeTargetOne := isLong ? close + effectiveTargetOneR * riskDistance : close - effectiveTargetOneR * riskDistance
    activeTargetTwo := isLong ? close + effectiveTargetTwoR * riskDistance : close - effectiveTargetTwoR * riskDistance
    targetOneTouched := false
    highestSinceEntry := close
    lowestSinceEntry := close

    string entryComment = profileTag + (isLong ? " BUY" : " SELL")
    string alertText = "IMSTE " + entryComment + " | score=" + str.tostring(isLong ? bullScore : bearScore, "#.0")
    if isLong
        strategy.entry("Bull Swing", strategy.long, comment = entryComment, alert_message = alertText)
    else
        strategy.entry("Bear Swing", strategy.short, comment = entryComment, alert_message = alertText)

    if not na(entryLine)
        line.delete(entryLine)
    if not na(stopLine)
        line.delete(stopLine)
    if not na(targetOneLine)
        line.delete(targetOneLine)
    if not na(targetTwoLine)
        line.delete(targetTwoLine)

    if showRiskLevels
        entryLine := line.new(bar_index, activeEntry, bar_index + 20, activeEntry, color = color.new(#2196f3, 15), width = 2)
        stopLine := line.new(bar_index, activeStop, bar_index + 20, activeStop, color = color.new(bearColor, 10), width = 2)
        targetOneLine := line.new(bar_index, activeTargetOne, bar_index + 20, activeTargetOne, color = color.new(bullColor, 35), style = line.style_dashed)
        targetTwoLine := line.new(bar_index, activeTargetTwo, bar_index + 20, activeTargetTwo, color = color.new(bullColor, 15), style = line.style_dashed)

if activeDirection != 0 and not na(activeEntryBar) and bar_index > activeEntryBar
    highestSinceEntry := math.max(nz(highestSinceEntry, high), high)
    lowestSinceEntry := math.min(nz(lowestSinceEntry, low), low)

if activeDirection == 1 and not targetOneTouched and not na(activeTargetOne) and not na(activeEntryBar) and bar_index > activeEntryBar and high >= activeTargetOne
    targetOneTouched := true
if activeDirection == -1 and not targetOneTouched and not na(activeTargetOne) and not na(activeEntryBar) and bar_index > activeEntryBar and low <= activeTargetOne
    targetOneTouched := true

if targetOneTouched and activeDirection != 0
    float breakevenStop = activeDirection == 1 ? activeEntry + breakevenBufferR * activeRisk : activeEntry - breakevenBufferR * activeRisk
    if moveStopToBreakeven
        activeStop := activeDirection == 1 ? math.max(activeStop, breakevenStop) : math.min(activeStop, breakevenStop)
    if useAtrTrailAfterTp1
        float trailStop = activeDirection == 1 ? highestSinceEntry - effectiveTrailAtr * safeAtr : lowestSinceEntry + effectiveTrailAtr * safeAtr
        activeStop := activeDirection == 1 ? math.max(activeStop, trailStop) : math.min(activeStop, trailStop)

float targetOneQty = math.min(targetOneQuantity, 99.0)
float targetTwoQty = 100.0 - targetOneQty

if enableOrders and strategy.position_size > 0 and activeDirection == 1
    strategy.exit("Bull TP1", "Bull Swing", stop = activeInitialStop, limit = activeTargetOne, qty_percent = targetOneQty, alert_message = "IMSTE BULL TP1/STOP")
    strategy.exit("Bull TP2", "Bull Swing", stop = activeStop, limit = activeTargetTwo, qty_percent = targetTwoQty, alert_message = "IMSTE BULL TP2/TRAIL")

if enableOrders and strategy.position_size < 0 and activeDirection == -1
    strategy.exit("Bear TP1", "Bear Swing", stop = activeInitialStop, limit = activeTargetOne, qty_percent = targetOneQty, alert_message = "IMSTE BEAR TP1/STOP")
    strategy.exit("Bear TP2", "Bear Swing", stop = activeStop, limit = activeTargetTwo, qty_percent = targetTwoQty, alert_message = "IMSTE BEAR TP2/TRAIL")

bool longTrendFailure = strategy.position_size > 0 and close < referenceVwap and close < emaFast and close[1] < referenceVwap[1] and close[1] < emaFast[1]
bool shortTrendFailure = strategy.position_size < 0 and close > referenceVwap and close > emaFast and close[1] > referenceVwap[1] and close[1] > emaFast[1]
bool timedExit = activeDirection != 0 and not na(activeEntryBar) and bar_index - activeEntryBar >= effectiveMaximumBars

if enableOrders and exitOnTrendFailure and longTrendFailure
    strategy.close("Bull Swing", comment = "TREND FAILURE", alert_message = "IMSTE BULL TREND FAILURE")
if enableOrders and exitOnTrendFailure and shortTrendFailure
    strategy.close("Bear Swing", comment = "TREND FAILURE", alert_message = "IMSTE BEAR TREND FAILURE")
if enableOrders and timedExit
    if strategy.position_size > 0
        strategy.close("Bull Swing", comment = "TIME EXIT", alert_message = "IMSTE BULL TIME EXIT")
    if strategy.position_size < 0
        strategy.close("Bear Swing", comment = "TIME EXIT", alert_message = "IMSTE BEAR TIME EXIT")

if enableOrders and time > backtestEnd and strategy.position_size != 0
    strategy.close_all(comment = "BACKTEST END", alert_message = "IMSTE BACKTEST END")

if strategy.position_size == 0 and strategy.position_size[1] != 0
    activeDirection := 0
    activeEntryBar := na
    activeEntry := na
    activeInitialStop := na
    activeStop := na
    activeRisk := na
    activeTargetOne := na
    activeTargetTwo := na
    targetOneTouched := false
    highestSinceEntry := na
    lowestSinceEntry := na

if showRiskLevels and activeDirection != 0
    int riskRightEdge = bar_index + 10
    if not na(entryLine)
        line.set_x2(entryLine, riskRightEdge)
    if not na(stopLine)
        line.set_x2(stopLine, riskRightEdge)
        line.set_y1(stopLine, activeStop)
        line.set_y2(stopLine, activeStop)
    if not na(targetOneLine)
        line.set_x2(targetOneLine, riskRightEdge)
    if not na(targetTwoLine)
        line.set_x2(targetTwoLine, riskRightEdge)

// ============================================================================
// MULTI-TIMEFRAME CONTEXT PANEL
// ============================================================================
int stateOneMinute = request.security(syminfo.tickerid, "1", f_contextState(9, 21, 100, 55.0, 45.0)[1], lookahead = barmerge.lookahead_on)
int stateFifteenMinute = request.security(syminfo.tickerid, "15", f_contextState(20, 50, 200, 53.0, 47.0)[1], lookahead = barmerge.lookahead_on)
int stateOneHour = request.security(syminfo.tickerid, "60", f_contextState(20, 50, 200, 52.0, 48.0)[1], lookahead = barmerge.lookahead_on)

var table mtfPanel = table.new(position.top_right, 2, 5, bgcolor = color.new(#10141c, 10), border_color = color.new(#607d8b, 55), border_width = 1)
if barstate.islast and showMtfPanel
    string currentSignalText = bullEntrySignal ? profileTag + " BUY" : bearEntrySignal ? profileTag + " SELL" : "WAIT"
    color currentSignalColor = bullEntrySignal ? bullColor : bearEntrySignal ? bearColor : color.silver
    table.cell(mtfPanel, 0, 0, "IMSTE CONTEXT", text_color = color.white, bgcolor = color.new(#1b2430, 0))
    table.cell(mtfPanel, 1, 0, currentSignalText, text_color = currentSignalColor, bgcolor = color.new(#1b2430, 0))
    table.cell(mtfPanel, 0, 1, "1 minute", text_color = color.silver)
    table.cell(mtfPanel, 1, 1, f_stateText(stateOneMinute), text_color = f_stateColor(stateOneMinute))
    table.cell(mtfPanel, 0, 2, "15 minute", text_color = color.silver)
    table.cell(mtfPanel, 1, 2, f_stateText(stateFifteenMinute), text_color = f_stateColor(stateFifteenMinute))
    table.cell(mtfPanel, 0, 3, "1 hour", text_color = color.silver)
    table.cell(mtfPanel, 1, 3, f_stateText(stateOneHour), text_color = f_stateColor(stateOneHour))
    table.cell(mtfPanel, 0, 4, "Profile / Score", text_color = color.silver)
    table.cell(mtfPanel, 1, 4, profileTag + "  " + str.tostring(math.max(bullScore, bearScore), "#.0"), text_color = math.max(bullScore, bearScore) >= effectiveMinimumScore ? color.white : color.silver)
else if barstate.islast and not showMtfPanel
    table.clear(mtfPanel, 0, 0, 1, 4)

// ============================================================================
// CHART DISPLAY
// ============================================================================
plot(showVWAP ? referenceVwap : na, "VWAP", color = color.new(vwapColor, 0), linewidth = 2, display = display.all - display.status_line)
plot(showFastEma ? emaFast : na, "Fast EMA", color = color.new(#2196f3, 25), linewidth = 1, display = display.all - display.status_line)

color candleColor = na
if showTrendColor
    candleColor := emaBull and htfBull and vwapBull ? color.new(bullColor, 20) : emaBear and htfBear and vwapBear ? color.new(bearColor, 20) : na
barcolor(candleColor)

if showEntryLabels and bullEntrySignal
    label.new(bar_index, low, profileTag + " BUY\n" + str.tostring(bullScore, "#"), style = label.style_label_up, color = color.new(bullColor, 0), textcolor = color.white, size = size.small, yloc = yloc.belowbar)
if showEntryLabels and bearEntrySignal
    label.new(bar_index, high, profileTag + " SELL\n" + str.tostring(bearScore, "#"), style = label.style_label_down, color = color.new(bearColor, 0), textcolor = color.white, size = size.small, yloc = yloc.abovebar)

var label vwapLabel = na
if barstate.islast
    if not na(vwapLabel)
        label.delete(vwapLabel)
    vwapLabel := showVWAP ? label.new(bar_index + rightLabelOffset, referenceVwap, f_levelText("VWAP", referenceVwap), xloc = xloc.bar_index, yloc = yloc.price, style = label.style_label_left, color = color.new(vwapColor, 10), textcolor = color.black, size = size.tiny) : na

// ============================================================================
// ALERTS
// ============================================================================
alertcondition(bullEntrySignal, "IMSTE Buy Signal", "IMSTE BUY on {{ticker}} {{interval}} at {{close}}")
alertcondition(bearEntrySignal, "IMSTE Sell Signal", "IMSTE SELL on {{ticker}} {{interval}} at {{close}}")
alertcondition(sellSideSweep, "Sell-Side Liquidity Sweep", "Sell-side liquidity sweep on {{ticker}} {{interval}}")
alertcondition(buySideSweep, "Buy-Side Liquidity Sweep", "Buy-side liquidity sweep on {{ticker}} {{interval}}")

if bullEntrySignal
    alert("IMSTE " + profileTag + " BUY | " + syminfo.ticker + " | score=" + str.tostring(bullScore, "#.0") + " | close=" + str.tostring(close, format.mintick), alert.freq_once_per_bar_close)
if bearEntrySignal
    alert("IMSTE " + profileTag + " SELL | " + syminfo.ticker + " | score=" + str.tostring(bearScore, "#.0") + " | close=" + str.tostring(close, format.mintick), alert.freq_once_per_bar_close)
