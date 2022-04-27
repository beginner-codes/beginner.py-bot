import dippy


class MemberCounterExtension(dippy.Extension):
    client: dippy.Client

    @dippy.Extension.listener("ready")
    async def on_ready(self):
        self.events.off("ready", self.on_ready.handler)
        self._update_member_counter()

    def _update_member_counter(self):
        self._schedule_update()
        self._run_update()

    def _run_update(self):
        self.client.loop.create_task(self._do_update())

    def _schedule_update(self):
        self.client.loop.call_later(600, self._run_update)

    async def _do_update(self):
        channel = self.client.get_channel(968972011407826954)
        guild = channel.guild
        members = sum(not member.bot for member in guild.default_role.members)
        await channel.edit(name=f"📊total-members-{members}")

