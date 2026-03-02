import { useState, useMemo } from 'react';
import { Flame, TrendingUp, Wallet, Calendar, PiggyBank, Target, DollarSign, Percent, AlertTriangle } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart, Legend } from 'recharts';

interface ProjectionData {
  month: number;
  year: number;
  assets: number;
  contributions: number;
  growth: number;
  debt: number;
  netWorth: number;
  label: string;
}

function formatCurrency(value: number): string {
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(1)}M`;
  } else if (value >= 1000) {
    return `$${(value / 1000).toFixed(0)}K`;
  }
  return `$${value.toFixed(0)}`;
}

function formatFullCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

function App() {
  const [currentSavings, setCurrentSavings] = useState<number>(50000);
  const [monthlyIncome, setMonthlyIncome] = useState<number>(8000);
  const [monthlyExpenses, setMonthlyExpenses] = useState<number>(4000);
  const [annualExpenses, setAnnualExpenses] = useState<number>(5000);
  const [expectedReturn, setExpectedReturn] = useState<number>(7);
  const [withdrawalRate, setWithdrawalRate] = useState<number>(4);
  const [currentDebt, setCurrentDebt] = useState<number>(0);
  const [debtInterestRate, setDebtInterestRate] = useState<number>(6);

  const calculations = useMemo(() => {
    const monthlyReturn = expectedReturn / 100 / 12;
    const monthlyDebtRate = debtInterestRate / 100 / 12;
    const monthlySavings = monthlyIncome - monthlyExpenses;
    const totalAnnualExpenses = (monthlyExpenses * 12) + annualExpenses;
    const fireNumber = totalAnnualExpenses / (withdrawalRate / 100);
    const savingsRate = monthlyIncome > 0 ? (monthlySavings / monthlyIncome) * 100 : 0;

    // Check if FIRE is achievable
    const canAchieveFire = monthlySavings > 0;

    // Calculate months to FIRE using future value formula
    let monthsToFire = 0;
    let projections: ProjectionData[] = [];

    if (canAchieveFire) {
      // Net worth = assets - debt
      let currentAssets = currentSavings;
      let remainingDebt = currentDebt;
      let totalContributions = currentSavings;
      let month = 0;
      const maxMonths = 600; // 50 years max

      while ((currentAssets - remainingDebt) < fireNumber && month < maxMonths) {
        // Debt accrues interest
        if (remainingDebt > 0) {
          remainingDebt = remainingDebt * (1 + monthlyDebtRate);
        }

        // Pay off debt first, then invest
        if (remainingDebt > 0 && monthlySavings > 0) {
          const debtPayment = Math.min(monthlySavings, remainingDebt);
          remainingDebt -= debtPayment;
          const investmentAmount = monthlySavings - debtPayment;
          const growth = currentAssets * monthlyReturn;
          currentAssets = currentAssets + growth + investmentAmount;
          totalContributions += investmentAmount;
        } else {
          const growth = currentAssets * monthlyReturn;
          currentAssets = currentAssets + growth + monthlySavings;
          totalContributions += monthlySavings;
        }
        month++;

        // Record data points at intervals
        const netWorth = currentAssets - remainingDebt;
        if (month % 12 === 0 || netWorth >= fireNumber) {
          projections.push({
            month,
            year: Math.floor(month / 12),
            assets: Math.round(currentAssets),
            contributions: Math.round(totalContributions),
            growth: Math.round(currentAssets - totalContributions),
            debt: Math.round(remainingDebt),
            netWorth: Math.round(netWorth),
            label: `Year ${Math.floor(month / 12)}`,
          });
        }
      }

      monthsToFire = month;

      // Add some projections beyond FIRE for context
      const additionalYears = 10;
      for (let i = 1; i <= additionalYears; i++) {
        for (let m = 0; m < 12; m++) {
          if (remainingDebt > 0) {
            remainingDebt = remainingDebt * (1 + monthlyDebtRate);
            const debtPayment = Math.min(monthlySavings, remainingDebt);
            remainingDebt -= debtPayment;
            const investmentAmount = monthlySavings - debtPayment;
            const growth = currentAssets * monthlyReturn;
            currentAssets = currentAssets + growth + investmentAmount;
            totalContributions += investmentAmount;
          } else {
            const growth = currentAssets * monthlyReturn;
            currentAssets = currentAssets + growth + monthlySavings;
            totalContributions += monthlySavings;
          }
          month++;
        }
        const netWorth = currentAssets - remainingDebt;
        projections.push({
          month,
          year: Math.floor(month / 12),
          assets: Math.round(currentAssets),
          contributions: Math.round(totalContributions),
          growth: Math.round(currentAssets - totalContributions),
          debt: Math.round(remainingDebt),
          netWorth: Math.round(netWorth),
          label: `Year ${Math.floor(month / 12)}`,
        });
      }
    }

    const yearsToFire = monthsToFire / 12;
    const fireDate = new Date();
    fireDate.setMonth(fireDate.getMonth() + monthsToFire);

    return {
      fireNumber,
      monthlySavings,
      savingsRate,
      yearsToFire,
      monthsToFire,
      fireDate,
      projections,
      canAchieveFire,
      totalAnnualExpenses,
      currentDebt,
    };
  }, [currentSavings, monthlyIncome, monthlyExpenses, annualExpenses, expectedReturn, withdrawalRate, currentDebt, debtInterestRate]);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="card-glass p-4 shadow-xl">
          <p className="text-white font-display font-semibold mb-2">{label}</p>
          <p className="text-wealth-400">Net Worth: {formatFullCurrency(payload[0]?.payload?.netWorth || 0)}</p>
          <p className="text-emerald-400">Assets: {formatFullCurrency(payload[0]?.payload?.assets || 0)}</p>
          {payload[0]?.payload?.debt > 0 && <p className="text-red-400">Debt: {formatFullCurrency(payload[0]?.payload?.debt || 0)}</p>}
          <p className="text-fire-400">Contributions: {formatFullCurrency(payload[0]?.payload?.contributions || 0)}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="min-h-screen p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8 md:mb-12">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="p-3 rounded-2xl bg-gradient-to-br from-fire-500 to-fire-700 shadow-lg shadow-fire-500/25">
              <Flame className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-4xl md:text-5xl font-display font-bold text-white">
              FIRE <span className="fire-gradient-text">Calculator</span>
            </h1>
          </div>
          <p className="text-slate-400 text-lg">Calculate your path to Financial Independence</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 md:gap-8">
          {/* Input Panel */}
          <div className="lg:col-span-1">
            <div className="card-glass p-6 md:p-8">
              <h2 className="text-xl font-display font-semibold text-white mb-6 flex items-center gap-2">
                <Wallet className="w-5 h-5 text-fire-400" />
                Your Finances
              </h2>

              <div className="space-y-5">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Current Savings
                  </label>
                  <div className="relative">
                    <DollarSign className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                    <input
                      type="number"
                      value={currentSavings}
                      onChange={(e) => setCurrentSavings(Number(e.target.value))}
                      className="input-field"
                      placeholder="50000"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Monthly Income
                  </label>
                  <div className="relative">
                    <DollarSign className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                    <input
                      type="number"
                      value={monthlyIncome}
                      onChange={(e) => setMonthlyIncome(Number(e.target.value))}
                      className="input-field"
                      placeholder="8000"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Monthly Expenses
                  </label>
                  <div className="relative">
                    <DollarSign className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                    <input
                      type="number"
                      value={monthlyExpenses}
                      onChange={(e) => setMonthlyExpenses(Number(e.target.value))}
                      className="input-field"
                      placeholder="4000"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Additional Annual Expenses
                  </label>
                  <div className="relative">
                    <DollarSign className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                    <input
                      type="number"
                      value={annualExpenses}
                      onChange={(e) => setAnnualExpenses(Number(e.target.value))}
                      className="input-field"
                      placeholder="5000"
                    />
                  </div>
                  <p className="text-xs text-slate-500 mt-1">Insurance, vacations, etc.</p>
                </div>

                <div className="pt-4 border-t border-white/10">
                  <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
                    <span className="text-red-400">Debt</span>
                  </h3>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-2">
                        Current Debt
                      </label>
                      <div className="relative">
                        <DollarSign className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                        <input
                          type="number"
                          value={currentDebt}
                          onChange={(e) => setCurrentDebt(Number(e.target.value))}
                          className="input-field"
                          placeholder="0"
                        />
                      </div>
                      <p className="text-xs text-slate-500 mt-1">Student loans, credit cards, etc.</p>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-2">
                        Debt Interest Rate
                      </label>
                      <div className="relative">
                        <Percent className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                        <input
                          type="number"
                          value={debtInterestRate}
                          onChange={(e) => setDebtInterestRate(Number(e.target.value))}
                          className="input-field"
                          placeholder="6"
                          step="0.5"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                <div className="pt-4 border-t border-white/10">
                  <h3 className="text-sm font-semibold text-slate-300 mb-4">Assumptions</h3>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-2">
                        Expected Annual Return
                      </label>
                      <div className="relative">
                        <Percent className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                        <input
                          type="number"
                          value={expectedReturn}
                          onChange={(e) => setExpectedReturn(Number(e.target.value))}
                          className="input-field"
                          placeholder="7"
                          step="0.5"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-2">
                        Safe Withdrawal Rate
                      </label>
                      <div className="relative">
                        <Percent className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                        <input
                          type="number"
                          value={withdrawalRate}
                          onChange={(e) => setWithdrawalRate(Number(e.target.value))}
                          className="input-field"
                          placeholder="4"
                          step="0.25"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Dashboard Panel */}
          <div className="lg:col-span-2 space-y-6">
            {/* Warning Banner */}
            {!calculations.canAchieveFire && (
              <div className="card-glass p-6 border-l-4 border-amber-500 bg-amber-500/10">
                <div className="flex items-start gap-4">
                  <AlertTriangle className="w-6 h-6 text-amber-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <h3 className="text-lg font-semibold text-amber-400">Expenses Exceed Income</h3>
                    <p className="text-slate-300 mt-1">
                      Your monthly expenses ({formatFullCurrency(monthlyExpenses)}) are greater than or equal to your income ({formatFullCurrency(monthlyIncome)}).
                      Reduce expenses or increase income to calculate a valid FIRE date.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Key Metrics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="metric-card">
                <div className="flex items-center gap-2 mb-3">
                  <Target className="w-5 h-5 text-fire-400" />
                  <span className="text-sm text-slate-400">FIRE Number</span>
                </div>
                <p className="text-2xl md:text-3xl font-display font-bold fire-gradient-text">
                  {formatCurrency(calculations.fireNumber)}
                </p>
              </div>

              <div className="metric-card">
                <div className="flex items-center gap-2 mb-3">
                  <Calendar className="w-5 h-5 text-wealth-400" />
                  <span className="text-sm text-slate-400">Years to FIRE</span>
                </div>
                <p className="text-2xl md:text-3xl font-display font-bold wealth-gradient-text">
                  {calculations.canAchieveFire ? calculations.yearsToFire.toFixed(1) : '—'}
                </p>
              </div>

              <div className="metric-card">
                <div className="flex items-center gap-2 mb-3">
                  <PiggyBank className="w-5 h-5 text-blue-400" />
                  <span className="text-sm text-slate-400">Savings Rate</span>
                </div>
                <p className="text-2xl md:text-3xl font-display font-bold text-blue-400">
                  {calculations.savingsRate.toFixed(0)}%
                </p>
              </div>

              <div className="metric-card">
                <div className="flex items-center gap-2 mb-3">
                  <TrendingUp className="w-5 h-5 text-purple-400" />
                  <span className="text-sm text-slate-400">Monthly Savings</span>
                </div>
                <p className="text-2xl md:text-3xl font-display font-bold text-purple-400">
                  {formatCurrency(calculations.monthlySavings)}
                </p>
              </div>
            </div>

            {/* FIRE Date Card */}
            {calculations.canAchieveFire && (
              <div className="card-glass p-6 bg-gradient-to-r from-fire-500/10 to-wealth-500/10">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                  <div>
                    <h3 className="text-lg text-slate-300">Your projected FIRE date</h3>
                    <p className="text-3xl md:text-4xl font-display font-bold text-white mt-2">
                      {calculations.fireDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
                    </p>
                  </div>
                  <div className="text-left md:text-right">
                    <p className="text-slate-400">Total annual expenses at FIRE</p>
                    <p className="text-xl font-semibold text-fire-400">
                      {formatFullCurrency(calculations.totalAnnualExpenses)}/year
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Projection Chart */}
            <div className="card-glass p-6">
              <h3 className="text-lg font-display font-semibold text-white mb-6 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-wealth-400" />
                Asset Projection Over Time
              </h3>

              {calculations.canAchieveFire && calculations.projections.length > 0 ? (
                <div className="h-80 md:h-96">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={calculations.projections}>
                      <defs>
                        <linearGradient id="colorAssets" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#22c55e" stopOpacity={0}/>
                        </linearGradient>
                        <linearGradient id="colorContributions" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#f97316" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#f97316" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis
                        dataKey="label"
                        stroke="#94a3b8"
                        tick={{ fill: '#94a3b8', fontSize: 12 }}
                      />
                      <YAxis
                        stroke="#94a3b8"
                        tick={{ fill: '#94a3b8', fontSize: 12 }}
                        tickFormatter={(value) => formatCurrency(value)}
                      />
                      <Tooltip content={<CustomTooltip />} />
                      <Legend
                        wrapperStyle={{ paddingTop: '20px' }}
                        formatter={(value) => <span className="text-slate-300">{value}</span>}
                      />
                      <Area
                        type="monotone"
                        dataKey="netWorth"
                        stroke="#22c55e"
                        strokeWidth={2}
                        fillOpacity={1}
                        fill="url(#colorAssets)"
                        name="Net Worth"
                      />
                      <Area
                        type="monotone"
                        dataKey="contributions"
                        stroke="#f97316"
                        strokeWidth={2}
                        fillOpacity={1}
                        fill="url(#colorContributions)"
                        name="Contributions"
                      />
                      {/* FIRE Number reference line */}
                      <Line
                        type="monotone"
                        dataKey={() => calculations.fireNumber}
                        stroke="#ef4444"
                        strokeDasharray="5 5"
                        strokeWidth={2}
                        dot={false}
                        name="FIRE Target"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="h-80 flex items-center justify-center text-slate-400">
                  <p>Adjust your finances to see projections</p>
                </div>
              )}
            </div>

            {/* Additional Info */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="card-glass p-6">
                <h4 className="text-sm font-semibold text-slate-300 mb-4">How FIRE Number is Calculated</h4>
                <p className="text-slate-400 text-sm leading-relaxed">
                  Your FIRE number is based on the {withdrawalRate}% safe withdrawal rate.
                  This means you need <span className="text-fire-400 font-semibold">{(100 / withdrawalRate).toFixed(0)}x</span> your
                  annual expenses saved to retire safely.
                </p>
                <div className="mt-4 p-3 bg-white/5 rounded-lg">
                  <code className="text-sm text-slate-300">
                    {formatFullCurrency(calculations.totalAnnualExpenses)} × {(100 / withdrawalRate).toFixed(0)} = {formatFullCurrency(calculations.fireNumber)}
                  </code>
                </div>
              </div>

              <div className="card-glass p-6">
                <h4 className="text-sm font-semibold text-slate-300 mb-4">The Power of Savings Rate</h4>
                <p className="text-slate-400 text-sm leading-relaxed">
                  Your savings rate of <span className="text-blue-400 font-semibold">{calculations.savingsRate.toFixed(0)}%</span> is
                  {calculations.savingsRate >= 50 ? ' excellent!' : calculations.savingsRate >= 30 ? ' good!' : calculations.savingsRate >= 15 ? ' a solid start.' : ' below average.'}
                  {' '}Every 10% increase in savings rate can reduce years to FIRE by 5-10 years.
                </p>
                <div className="mt-4 p-3 bg-white/5 rounded-lg">
                  <code className="text-sm text-slate-300">
                    ({formatFullCurrency(monthlyIncome)} - {formatFullCurrency(monthlyExpenses)}) / {formatFullCurrency(monthlyIncome)} = {calculations.savingsRate.toFixed(1)}%
                  </code>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-12 text-slate-500 text-sm">
          <p>Based on historical market returns. Past performance does not guarantee future results.</p>
        </div>
      </div>
    </div>
  );
}

export default App;
