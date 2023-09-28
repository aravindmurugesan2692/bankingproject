resource "aws_instance" "test-server" {
  ami           = "ami-08e5424edfe926b43" 
  instance_type = "insureme" 
  key_name = "insureme"
  vpc_security_group_ids= ["sg-0ff4024a0cba88baf"]
  connection {
    type     = "ssh"
    user     = "ec2-user"
    private_key = file("./insureme.pem")
    host     = self.public_ip
  }
  provisioner "remote-exec" {
    inline = [ "echo 'wait to start instance' "]
  }
  tags = {
    Name = "test-server"
  }
  provisioner "local-exec" {
        command = " echo ${aws_instance.test-server.public_ip} > inventory "
  }
   provisioner "local-exec" {
  command = "ansible-playbook /var/lib/jenkins/workspace/Banking-Project/my-serverfiles/finance-playbook.yml "
  } 
}
