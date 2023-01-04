FROM quay.io/tripleomastercentos9/openstack-tripleo-ansible-ee:current-tripleo

USER root

# Test
# ADD ping.yaml ./project


USER root
RUN ansible-galaxy collection install cloudguruab.edpm_plugin 
RUN chmod -R 777 /usr/share/ansible
ADD entrypoint.sh /bin/tripleo_entrypoint
RUN chmod +x /bin/tripleo_entrypoint
USER 1001
