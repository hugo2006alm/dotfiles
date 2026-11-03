from dotfiles_api.domain.models.repair_plan import RepairPlan


class RepairService:
    SAFE = {"configure", "link", "session", "portal"}

    def __init__(self, doctor, actions):
        self.doctor, self.actions = doctor, actions

    def plan(self, dry_run=False):
        return RepairPlan(self.doctor.run(dry_run=dry_run))

    def apply(self, plan_id):
        if not plan_id:
            raise ValueError("Review repair --plan, then pass --apply --plan-id ID")
        plan = self.plan()
        if plan.id != plan_id:
            raise ValueError("Repair plan changed; run repair --plan and review it again")
        plan.describe()
        for item in plan.operations:
            name, *args = item.repair
            if item.privileged or name not in self.SAFE or name not in self.actions:
                print(f"Manual repair required: {item.message}")
                continue
            self.actions[name](args)
        return self.doctor.run()
