class SchedulingAgent:
    def schedule(self, order):
        print("\n[SchedulingAgent]")
        print(
            f"Order {order['order_id']} scheduled. "
            f"ETA: {order['eta_minutes']} minutes."
        )
