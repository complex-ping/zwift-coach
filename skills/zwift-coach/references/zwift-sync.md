# Intervals.icu and Zwift sync

Setup is once only: in Intervals.icu settings, open the Zwift box and choose Connect.

- **Where workouts appear:** on the Zwift home screen for today, and under Workouts → Custom → Intervals.icu.
- **Window:** only the next 7 days are uploaded, rolling daily. A later workout is on the Intervals calendar but not in Zwift yet. This is normal.
- **Indoor tag:** workouts without it may be refused by Zwift. Plan events carry the `indoor` tag.
- **FTP:** not synced. Targets are % of FTP, so FTP must match in Zwift and Intervals.icu, or watts will differ.
- **Targets:** cadence targets sync. HR targets don't, so keep plan workouts power-based.
- **Rides coming back:** the direct Zwift connection sends activities to Intervals.icu, and those are readable by the API. Activities imported only from Strava are not.

If a workout is missing in Zwift, check in this order:

1. Is it within 7 days?
2. Does it have the `indoor` tag and a parsed workout?
3. Does Intervals.icu settings allow uploads for that workout type?
4. Has Zwift been restarted since the sync?

Fallback: the workout can be exported as a `.zwo` file from Intervals.icu and copied to the Zwift workouts folder.
